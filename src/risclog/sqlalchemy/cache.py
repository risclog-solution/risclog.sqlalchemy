import csv
import gc
import io
import sys

import sqlalchemy
from risclog.sqlalchemy.model import ObjectBase
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import attributes


class MultipleObjectsFoundException(Exception):
    """Raised when a single result was expected but multiple were found."""

    pass


class ModelCache:
    """
    A cache for SQLAlchemy ORM model instances, used to enhance performance
    when working with a large number of database operations.

    Database requests are reduced to a fetching request per model
    (requesting all model instances) and an updating/inserting request when
    `save_changes` is called.
    To achieve this, model instance references are stored and continually
    indexed by the attributes they have been filtered on.

    Use the methods `get()`, `find()`, `create()` and `get_or_create()` to
    query the cache or insert new instances. Use `save_changes()` to flush
    changes to the database and clearing the cache.

    For setup, `ModelCache` currently needs some metadata about the models
    it should handle. Namely, the order in which models will be saved should
    be specified by an iterable (`save_order`). Use this to handle foreign key
    dependencies between your tables.
    Additionally, a dictionary `sequences` specifies model attributes and
    corresponding sequences that will be set during flushing. Use this for
    example for primary keys that normally are set automatically when creating
    a new table row.

    For performance gains, `save_changes()` flushes by using SQLAlchemy's bulk
    functionality and/or psycopg2's `copy_expert` method which explicitly
    reduces the ORM behavior.
    Make sure to not use model instances after you have flushed them. These
    instances are neither connected to a session nor are they updated
    accordingly.
    For more information, see:
    https://docs.sqlalchemy.org/en/13/orm/persistence_techniques.html#bulk-operations
    """

    def __init__(
        self,
        save_order,
        sequences,
        session,
        engine_name,
        prefetch=None,
        preload_models=True,
        preload_models_data={},
        preload_models_filter={},
        logger=None,
        use_copy=False,
        check_memory_usage=False,
    ):
        """
        Args:
            save_order: Iterable of model names, specifying the order in
                        which models will be saved. Used to solve dependency
                        constraints.
            sequences: Dictionary that matches models' attributes to
                       database sequences that are set automatically on
                       flushing.
                       Example: {'Model': (('attribute', 'sequence'), )}
            session: SQLAlchemy session used for flushing by default.
            prefetch: Specifies if certain relations should be prefetched.
            engine_name: Name of the engine used for sequence fetching.
                         Dictionary mapping model names to tuples of columns.
            preload_models: Preloads existing model instances on setup if True.
            use_copy: Use PostgreSQL's COPY command to insert new instances if
                      True.
        """
        self._save_order = save_order
        self._sequences = sequences
        self.session = session
        self._engine_name = engine_name
        self._prefetch = prefetch
        self._preload_models = preload_models
        self._preload_models_data = preload_models_data
        self._preload_models_filter = preload_models_filter
        self._logger = logger
        self._use_copy = use_copy
        self._cached_instances = {}
        self._indices = {}

        if check_memory_usage:
            from guppy import hpy

            self.hp = hpy()
            self.hp.setrelheap()

    def __sizeof__(self):
        if not hasattr(self, 'hp'):
            return 0

        h = self.hp.heap()
        return h.size

    def _sizeof_fmt(self, num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return f'{num:3.1f} {unit}{suffix}'
            num /= 1024.0
        return f'{num:.1f}Yi{suffix}'

    def log_memory_usage(self):
        if not hasattr(self, 'hp'):
            return

        bsize = sys.getsizeof(self)
        size = self._sizeof_fmt(bsize)
        self._log('info', f'Memory usage: {size} ({bsize})')

    def find(self, model, **kwargs):
        """
        Find `model` instances with matching `kwargs`.

        Returns:
            A list of matching `model` instances or an empty list.
        """
        attribute_index = self._get_attribute_index(model, kwargs.keys())
        instance_key = tuple(kwargs[attr] for attr in sorted(kwargs.keys()))
        return attribute_index.get(instance_key, [])

    def get(self, model, **kwargs):
        """
        Find a single `model` instance witch matching `kwargs`.

        Returns:
            A matching `model` instance or None.

        Raises:
            MultipleObjectsFoundException: Multiple objects were found.
        """
        result = self.find(model, **kwargs)
        if len(result) == 0:
            return None
        elif len(result) > 1:
            raise MultipleObjectsFoundException()
        return result[0]

    def create(self, model, **kwargs):
        """
        Create a `model` instance with `kwargs` as attributes.

        Returns:
            The newly created `model` instance.
        """
        model_cache = self._get_model_cache(model)
        model_indices = self._get_model_indices(model)

        instance = model(**kwargs)
        model_cache.append(instance)

        for attribute_key in model_indices.keys():
            instance_key = self._object_instance_key(instance, attribute_key)
            cache = model_indices[attribute_key].setdefault(instance_key, [])
            if instance not in cache:
                cache.append(instance)

        return instance

    def get_or_create(self, model, **kwargs):
        """
        Find or create a `model` instance witch matching `kwargs`.

        Returns:
            A matching or newly created `model` instance.

        Raises:
            MultipleObjectsFoundException: Multiple objects were found.
        """
        instance = self.get(model, **kwargs)
        if instance is not None:
            return instance
        else:
            return self.create(model, **kwargs)

    def save_changes(self, session=None, cursor=None):
        """
        Flush modified and created object to the database before clearing the
        cache.

        Args:
            session: A SQLAlchemy session to use instead of the default one.
        """
        self.log_memory_usage()

        if session is None:
            session = self.session
        if cursor is None and self._use_copy:
            cursor = (
                self.session.using_bind(self._engine_name)
                .connection()
                .connection.cursor()
            )

        self._log('debug', 'Flushing model cache.')
        self._assign_sequences()
        self._sync_relationship_attrs()

        for model_name in self._save_order:
            if model_name not in self._cached_instances:
                continue
            objects = self._cached_instances[model_name]
            objects = self._filter_sa_result_objects(objects)
            if len(objects) == 0:
                continue

            self._deregister_change_handler(
                type(objects[0]), self._instance_change_handler
            )
            new_objects, updated_objects = [], []

            for object in objects:
                if attributes.instance_state(object).key is None:
                    new_objects.append(object)
                else:
                    updated_objects.append(object)

            if self._use_copy:
                self._save_by_copy(cursor, new_objects)
            else:
                session.bulk_save_objects(new_objects)
            session.bulk_save_objects(updated_objects)
            session.flush()

        if self._use_copy:
            cursor.connection.commit()

        self.clear(session)
        self._log('info', 'Flushed model cache.')

    def _save_by_copy(self, cursor, objects):
        """
        Insert objects by using PostgreSQL's COPY command. This is
        database-specific but one of the most efficient ways to populate a
        table. Expects instances of one single model per call.
        See: https://www.postgresql.org/docs/current/sql-copy.html

        Args:
            cursor: A Psycopg2 cursor
            objects: SQLAlchemy ORM instances to save
        """
        if len(objects) == 0:
            return

        model = inspect(objects[0]).mapper
        for table in model.tables:
            file = io.StringIO()
            writer = csv.DictWriter(file, table.columns.keys())
            columns = [
                c
                for c in model.c.items()
                if c[1].table == table or c[1].primary_key
            ]

            for object in objects:
                row = {}
                for attr, column in columns:
                    value = getattr(object, attr)
                    if value is None:
                        if column.default is not None:
                            value = column.default.arg
                        else:
                            value = r'\N'
                    elif type(value) != column.type.python_type:
                        value = column.type.python_type(value)
                    row[column.key] = value
                writer.writerow(row)

            file.seek(0)

            columns_string = ','.join(
                [f'"{column}"' for column in table.columns.keys()]
            )
            cursor.copy_expert(
                f'COPY {table} ({columns_string}) '
                "FROM STDIN WITH CSV DELIMITER ',' NULL '\\N'",
                file,
            )
            cursor.connection.commit()

    def clear(self, session=None):
        """Clear the cache. Will result in data loss of unflushed objects."""
        self._cached_instances.clear()
        self._indices.clear()
        gc.collect()
        self.log_memory_usage()

    def _get_model_cache(self, model):
        """
        Return a list of every existing and newly created instance of `model`.
        """
        model_key = self._model_key(model)

        if model_key not in self._cached_instances:
            # Initialize model cache if it doesn't exist yet.
            if model_key in self._preload_models_data:
                query = model.query(*self._preload_models_data[model_key])
            else:
                query = model.query()

            if model_key in self._preload_models_filter:
                query = query.filter(self._preload_models_filter[model_key])

            if self._prefetch is not None and model_key in self._prefetch:
                query = query.options(
                    sqlalchemy.orm.joinedload(
                        *[attr for attr in self._prefetch[model_key]]
                    )
                )

            if self._preload_models:
                self._cached_instances[model_key] = query.all()
            else:
                # XXX: We run a noop DB request here to avoid some
                # hard-to-debug session transaction errors that crop up
                # otherwise.
                self._cached_instances[model_key] = query.limit(0).all()

            self._register_change_handler(model, self._instance_change_handler)

        return self._cached_instances[model_key]

    def _get_model_indices(self, model):
        """
        Return a dictionary containing tuples of indexed attributes as keys.
        """
        model_key = self._model_key(model)
        if model_key not in self._indices:
            self._indices[model_key] = {}
        return self._indices[model_key]

    def _get_attribute_index(self, model, attributes):
        """
        Return a dictionary containing model attribute values as keys and a
        list of matching instances as values.
        """
        model_indices = self._get_model_indices(model)
        attribute_key = tuple(sorted(attributes))

        if attribute_key not in model_indices:
            model_cache = self._get_model_cache(model)
            indexed_instances = {}
            for instance in model_cache:
                instance_key = self._object_instance_key(
                    instance, attribute_key
                )
                cache = indexed_instances.setdefault(instance_key, [])
                cache.append(instance)
            model_indices[attribute_key] = indexed_instances

        return model_indices[attribute_key]

    def _model_key(self, model):
        """
        Return the key used to reference a given `model` in the instance cache
        and indices.
        """
        return model.__name__

    def _object_instance_key(self, instance, attribute_key, replace=None):
        """
        Return the index key to reference a given `instance`given an
        `attribute_key`.
        """
        attributes = {name: getattr(instance, name) for name in attribute_key}
        if replace is not None:
            attributes.update(replace)
        return tuple(attributes[name] for name in attribute_key)

    def _assign_sequences(self):
        """
        Assign sequence values to empty model attributes specified in the
        constructor.

        This iterates over every cached model and its corresponding sequences
        and assigns sequence values where applicable..
        Empty sequence attributes are counted and matching sequence values are
        fetched from the database in a single request.
        """
        for model_name, objects in self._cached_instances.items():
            if model_name not in self._sequences:
                continue

            model_sequences = self._sequences[model_name]
            for sequence in model_sequences:
                new_objects = list(
                    filter(lambda o: getattr(o, sequence[0]) is None, objects)
                )
                if len(new_objects) > 0:
                    sequence_values = self.session.using_bind(
                        self._engine_name
                    ).execute(
                        "select nextval('%s') from generate_series(1,%s)"
                        % (sequence[1], len(new_objects))
                    )

                    for object, value in zip(new_objects, sequence_values):
                        setattr(object, sequence[0], value[0])

    def _filter_sa_result_objects(self, objects):
        return list(filter(lambda x: isinstance(x, ObjectBase), objects))

    def _sync_relationship_attrs(self):
        """
        Synchronize relationship attributes with their corresponding ID
        attributes.

        When using SQLAlchemy bulk functionality, the ORM behavior is changed
        in multiple ways. One important change is that relationship attributes
        aren't evaluated anymore.
        To still handle related object as expected, we iterate over
        relationship attributes and set their corresponding ID attributes on
        the same object.
        """
        for objects in self._cached_instances.values():
            objects = self._filter_sa_result_objects(objects)
            if len(objects) == 0:
                continue
            model = type(list(objects)[0])

            rel_map = [
                (rel.key, pair[1].key, pair[0].key)
                for rel in inspect(model).relationships
                for pair in rel.local_remote_pairs
                if rel.direction is not sqlalchemy.orm.interfaces.ONETOMANY
            ]
            for object in objects:
                for from_obj, from_attr, to_attr in rel_map:
                    if getattr(object, to_attr, None) is None:
                        setattr(
                            object,
                            to_attr,
                            getattr(
                                getattr(object, from_obj), from_attr, None
                            ),
                        )

    def _register_change_handler(self, model, event_handler):
        """Register an event handler for every column of a model."""
        for attr in inspect(model).column_attrs:
            sqlalchemy.event.listen(attr, 'set', event_handler)

    def _deregister_change_handler(self, model, event_handler):
        """Removes an event handler for every column of a model."""
        for attr in inspect(model).column_attrs:
            sqlalchemy.event.listen(attr, 'set', event_handler)

    def _instance_change_handler(self, instance, value, oldvalue, initiator):
        """
        Re-index model instances that were changed
        (to keep the index up-to-date).
        Called by SQLAlchemy's model `set` event which fires when a model
        attribute was changed. For more information,
        see: https://docs.sqlalchemy.org/en/13/orm/events.html
        """  # noqa: E501
        if oldvalue is sqlalchemy.util.symbol('NEVER_SET'):
            return

        model = type(instance)
        changed_attr = initiator.key
        model_indices = self._get_model_indices(model)

        for attribute_key in model_indices.keys():
            if changed_attr not in attribute_key:
                continue

            old_instance_key = self._object_instance_key(
                instance, attribute_key, replace={changed_attr: oldvalue}
            )
            new_instance_key = self._object_instance_key(
                instance, attribute_key, replace={changed_attr: value}
            )

            old_cache = model_indices[attribute_key].get(old_instance_key, [])
            if len(old_cache) > 1:
                old_cache.remove(instance)
            else:
                model_indices[attribute_key].pop(old_instance_key, [])

            cache = model_indices[attribute_key].setdefault(
                new_instance_key, []
            )
            if instance not in cache:
                cache.append(instance)

    def _log(self, level, message):
        """Send `message` to logger on `level` if set on setup."""
        if self._logger is not None:
            getattr(self._logger, level)(message)
