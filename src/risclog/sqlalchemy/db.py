import os

import alembic.config
import alembic.environment
import alembic.migration
import alembic.script
import risclog.sqlalchemy.interfaces
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import transaction
import zope.component
import zope.interface
import zope.sqlalchemy
from packaging.version import Version as parse_version
from sqlalchemy import __version__ as sqlalchemy_version

# Mapping engine name registered using Database.register_engine --> base class
_ENGINE_CLASS_MAPPING = {}

SA_GE_14 = parse_version(sqlalchemy_version) >= parse_version('1.4.0')


def assert_engine_not_registered(name, mapping):
    """Ensure a consistent error message."""
    assert (
        name not in mapping
    ), f'An engine for name `{name}` is already registered.'


def register_class(class_):
    """Register a (base) class for an engine."""
    name = class_._engine_name
    assert_engine_not_registered(name, _ENGINE_CLASS_MAPPING)
    _ENGINE_CLASS_MAPPING[name] = class_


def unregister_class(class_):
    """Clear registration of a (base) class for an engine."""
    del _ENGINE_CLASS_MAPPING[class_._engine_name]


class RoutingSession(sqlalchemy.orm.Session):
    """Session which routes mapped objects to the correct database engine."""

    _name = None

    def get_bind(
        self,
        mapper=None,
        clause=None,
        bind=None,
        _sa_skip_events=None,
        _sa_skip_for_implicit_returning=False,
    ):
        if bind:
            return bind
        db_util = zope.component.getUtility(
            risclog.sqlalchemy.interfaces.IDatabase
        )
        if self._name:
            # Engine was set using self.using_bind:
            return db_util.get_engine(self._name)
        if not mapper:
            if len(_ENGINE_CLASS_MAPPING) == 1:
                return db_util.get_engine(
                    list(_ENGINE_CLASS_MAPPING.keys())[0]
                )
            raise RuntimeError(
                "Don't know how to determine engine, no mapper."
            )

        for engine_name, class_ in _ENGINE_CLASS_MAPPING.items():
            if issubclass(mapper.class_, class_):
                return db_util.get_engine(engine_name)

        raise RuntimeError(f'Did not find an engine for {mapper.class_}')

    def _bound_execute(self, bind, *args, **kwargs):
        if SA_GE_14:
            return self.execute(*args, bind_arguments={'bind': bind}, **kwargs)
        else:
            return self.execute(*args, bind=bind, **kwargs)

    def execute_with_bind(self, engine_name, *args, **kwargs):
        """
        Execute a statement using a specific engine, indicated by its name.
        """
        db_util = zope.component.getUtility(
            risclog.sqlalchemy.interfaces.IDatabase
        )
        bind = db_util.get_engine(engine_name)
        return self._bound_execute(bind, *args, **kwargs)

    def using_bind(self, name):
        """
        Return session-like object that limits its action to the given engine.

        This method is deprecated and is kept for backward compatibility.
        If you need to execute a statement using a specific engine, use
        `execute_with_bind` instead.
        """

        class BoundSession:
            """
            Shim that maps a subset of commonly used SQLAlchemy session methods
            to the original session while forcing the bind.
            """

            def __init__(self, session, engine_name):
                self.session = session
                db_util = zope.component.getUtility(
                    risclog.sqlalchemy.interfaces.IDatabase
                )
                self.bind = db_util.get_engine(engine_name)

            def execute(self, *args, **kwargs):
                return self.session._bound_execute(self.bind, *args, **kwargs)

            def query(self, *args, **kwargs):
                # Associate query with this shim-session, to make it use its
                # `execute` method.
                query = self.session.query(*args, **kwargs).with_session(self)
                # Used to introspect if a query is bound to a specific engine.
                query._bind = self.bind
                return query

            def connection(self):
                bind = self.session.get_bind(bind=self.bind)
                return self.session._connection_for_bind(bind)

        return BoundSession(self, name)


def get_database(testing=False, keep_session=False, expire_on_commit=False):
    """Get or create the database utility."""
    if testing and not keep_session and not expire_on_commit:
        # Keep the old testing behaviour by default
        keep_session = True
        expire_on_commit = True
    db = zope.component.queryUtility(risclog.sqlalchemy.interfaces.IDatabase)
    if db is None:
        db = Database(testing, keep_session, expire_on_commit)
    assert (
        db.testing == testing
    ), 'Requested testing status `%s` does not match Database.testing.' % (
        testing
    )
    return db


@zope.interface.implementer(risclog.sqlalchemy.interfaces.IDatabase)
class Database:
    def __init__(
        self, testing=False, keep_session=False, expire_on_commit=False
    ):
        assert (
            zope.component.queryUtility(
                risclog.sqlalchemy.interfaces.IDatabase
            )
            is None
        ), (
            'Cannot create Database twice, use `.get_database()` to get '
            'the instance.'
        )
        self._engines = {}
        self.testing = testing
        self.session_factory = sqlalchemy.orm.scoped_session(
            sqlalchemy.orm.sessionmaker(
                class_=RoutingSession, expire_on_commit=expire_on_commit
            )
        )
        self.zope_transaction_events = zope.sqlalchemy.register(
            self.session_factory, keep_session=keep_session
        )
        self._setup_utility()

    def register_engine(
        self, dsn, engine_args={}, name='', alembic_location=None
    ):
        assert_engine_not_registered(name, self._engines)
        engine_args['echo'] = bool(
            int(os.environ.get('ECHO_SQLALCHEMY_QUERIES', '0'))
        )
        engine = sqlalchemy.create_engine(dsn, **engine_args)
        self._verify_engine(engine)
        self._engines[name] = dict(
            engine=engine, alembic_location=alembic_location
        )
        # Some model classes may already have been constructed without having
        # had access to a db engine so far, so give them a chance to do the
        # reflection now.
        self.prepare_deferred(_ENGINE_CLASS_MAPPING.get(name))

    def get_engine(self, name=''):
        return self._engines[name]['engine']

    def get_all_engines(self):
        return [x['engine'] for x in self._engines.values()]

    def drop_engine(self, name=''):
        engine = self.get_engine(name)
        engine.dispose()
        del self._engines[name]

    def prepare_deferred(self, class_):
        if class_ is None:
            return
        if issubclass(class_, sqlalchemy.ext.declarative.DeferredReflection):
            class_.prepare(self.get_engine(class_._engine_name))

    def create_all(self, engine_name='', create_defaults=True):
        """Create all tables etc. for an engine."""
        engine = self._engines[engine_name]
        _ENGINE_CLASS_MAPPING[engine_name].metadata.create_all(
            engine['engine']
        )

        # mark the database to be in the latest revision
        location = engine['alembic_location']
        if location:
            with alembic_context(engine['engine'], location) as ac:
                ac.migration_context.stamp(
                    ac.script, ac.script.get_current_head()
                )
        if create_defaults:
            self.create_defaults(engine_name)

    def create_defaults(self, engine_name=''):
        for name, class_ in risclog.sqlalchemy.model.class_registry.items():
            # do not call create_defaults for foreign engines,
            # since they may not be set up yet
            if engine_name != getattr(class_, '_engine_name', NotImplemented):
                continue
            if hasattr(class_, 'create_defaults'):
                class_.create_defaults()

    def _verify_engine(self, engine):
        # Step 1: Try to identify a testing table
        conn = engine.connect()
        from sqlalchemy import text

        try:
            conn.execute(text('SELECT * FROM tmp_functest'))
        except sqlalchemy.exc.DatabaseError:
            db_is_testing = False
        else:
            db_is_testing = True
        conn.invalidate()

        if self.testing and db_is_testing:
            # We're running as a test and it is a test dabase. Continue
            return
        if not self.testing and not db_is_testing:
            # We're running as a production system and we have a production
            # database. Continue.
            return

        # We're not in a valid state. Bail out.
        raise SystemExit(
            'Not working against correct database (live vs '
            'testing). Refusing to set up database connection '
            'to {}.'.format(engine.url)
        )

    def assert_database_revision_is_current(self, engine_name=''):
        def assert_revision(ac, head_rev, db_rev):
            if head_rev != db_rev:
                raise ValueError(
                    'Database revision {} of engine "{}" does not match '
                    'current revision {}.\nMaybe you want to call '
                    '`bin/alembic upgrade head`.'.format(
                        db_rev, engine_name, head_rev
                    )
                )

        self._run_in_alembic_context(assert_revision, engine_name)

    def update_database_revision_to_current(self, engine_name=''):
        def upgrade_revision(ac, head_rev, db_rev):
            if head_rev != db_rev:
                ac.upgrade(head_rev)

        self._run_in_alembic_context(upgrade_revision, engine_name)

    @property
    def session(self):
        return self.session_factory()

    def add(self, obj):
        return self.session.add(obj)

    def delete(self, obj):
        return self.session.delete(obj)

    def query(self, *args, **kw):
        return self.session.query(*args, **kw)

    def _setup_utility(self):
        zope.component.provideUtility(self)

    def _teardown_utility(self):
        zope.component.getGlobalSiteManager().unregisterUtility(self)

    def empty(
        self,
        engine,
        table_names=None,
        cascade=False,
        restart_sequences=True,
        empty_alembic_version=False,
        commit=True,
    ):
        transaction.abort()
        if table_names is None:
            inspector = sqlalchemy.inspect(engine)
            table_names = inspector.get_table_names()

            try:
                # never truncate the PostGIS table
                table_names.remove('spatial_ref_sys')
            except ValueError:
                pass

            if not empty_alembic_version:
                # Don't truncate alembic-version (unless explicitly asked to).
                # Ususally it does not make sense to clear it, because TRUNCATE
                # does not change the schema. Clearing the alembic_version will
                # cause "confusion and delay".
                try:
                    table_names.remove('alembic_version')
                except ValueError:
                    pass
        if not table_names:
            return
        tables = ', '.join('"%s"' % x for x in table_names)
        self.session._bound_execute(
            engine,
            'TRUNCATE {} {} {}'.format(
                tables,
                'RESTART IDENTITY' if restart_sequences else '',
                'CASCADE' if cascade else '',
            ),
        )
        zope.sqlalchemy.mark_changed(self.session)
        if commit:
            transaction.commit()

    def _run_in_alembic_context(self, func, engine_name=''):
        """Run a function in `alembic_context`.

        The function must take three parameters:
        * ac ... AlembicContext object
        * head_rev ... revision of alembic head
        * db_rev ... revision of database

        """
        engine = self._engines[engine_name]
        location = engine['alembic_location']
        if not location:
            return
        with alembic_context(engine['engine'], location) as ac:
            head_rev = ac.script.get_current_head()
            db_rev = ac.migration_context.get_current_revision()
            return func(ac, head_rev, db_rev)


class alembic_context:
    def __init__(self, engine, script_location):
        self.engine = engine
        self.script_location = script_location

    def __enter__(self):
        self.conn = conn = self.engine.connect()
        return AlembicContext(conn, self.script_location)

    def __exit__(self, exc_type, exc_value, tb):
        self.conn.close()
        if exc_type is not None:
            transaction.doom()
            raise exc_value


class AlembicContext:
    def __init__(self, conn, script_location):
        self.conn = conn
        self.config = alembic.config.Config()
        self.config.set_main_option('script_location', script_location)
        self.migration_context = alembic.migration.MigrationContext.configure(
            conn
        )
        self.script = alembic.script.ScriptDirectory.from_config(self.config)

    def upgrade(self, dest_rev):
        """Upgrade from current to `dest_rev`."""

        def upgrade_fn(rev, context):
            return self.script._upgrade_revs(dest_rev, rev)

        with alembic.environment.EnvironmentContext(
            self.config, self.script, fn=upgrade_fn, destination_rev=dest_rev
        ) as ec:
            ec.configure(self.conn)
            ec.run_migrations()
