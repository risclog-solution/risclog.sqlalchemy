from zope.component._compat import _BLANK
import alembic.config
import alembic.migration
import alembic.script
import os
import risclog.sqlalchemy.interfaces
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import transaction
import zope.component
import zope.interface
import zope.sqlalchemy


# Mapping engine name registered using Database.register_engine --> base class
_ENGINE_CLASS_MAPPING = {}


def register_class(class_):
    """Register a (base) class for an engine."""
    name = class_._engine_name
    assert name not in _ENGINE_CLASS_MAPPING, \
        'Registering name `{}` again.'.format(name)
    _ENGINE_CLASS_MAPPING[name] = class_


def unregister_class(class_):
    """Clear registration of a (base) class for an engine."""
    del _ENGINE_CLASS_MAPPING[class_._engine_name]


class RoutingSession(sqlalchemy.orm.Session):
    """Session which routes mapped objects to the correct database engine."""
    def get_bind(self, mapper=None, clause=None):
        db_util = zope.component.getUtility(
            risclog.sqlalchemy.interfaces.IDatabase)

        if not mapper:
            if len(_ENGINE_CLASS_MAPPING) == 1:
                return db_util.get_engine(
                    list(_ENGINE_CLASS_MAPPING.keys())[0])
            raise RuntimeError(
                "Don't know how to determine engine, no mapper.")

        for engine_name, class_ in _ENGINE_CLASS_MAPPING.items():
            if issubclass(mapper.class_, class_):
                return db_util.get_engine(engine_name)

        raise RuntimeError(
            "Did not find an engine for {}".format(mapper.class_))


def get_database(testing=False):
    """Get or create the database utility."""
    db = zope.component.queryUtility(
        risclog.sqlalchemy.interfaces.IDatabase)
    if db is None:
        db = Database(testing)
    assert db.testing == testing, \
        'Requested testing status `%s` does not match Database.testing.' % (
            testing)
    return db


@zope.interface.implementer(risclog.sqlalchemy.interfaces.IDatabase)
class Database(object):

    def __init__(self, testing=False):
        assert zope.component.queryUtility(
            risclog.sqlalchemy.interfaces.IDatabase) is None, \
            'Cannot create Database twice, use `.get_database()` to get '\
            'the instance.'
        self._engines = {}
        self.testing = testing
        self.session_factory = sqlalchemy.orm.scoped_session(
            sqlalchemy.orm.sessionmaker(
                class_=RoutingSession,
                extension=zope.sqlalchemy.ZopeTransactionExtension(
                    keep_session=testing)))
        self._setup_utility()

    def register_engine(self, dsn, engine_args={}, name=_BLANK,
                        alembic_location=None):
        assert name not in self._engines, \
            'Registering name `{}` again.'.format(name)
        engine_args['echo'] = bool(int(os.environ.get(
            'ECHO_SQLALCHEMY_QUERIES', '0')))
        engine = sqlalchemy.create_engine(dsn, **engine_args)
        self._verify_engine(engine)
        self._engines[name] = dict(
            engine=engine, alembic_location=alembic_location)
        # Some model classes may already have been constructed without having
        # had access to a db engine so far, so give them a chance to do the
        # reflection now.
        self.prepare_deferred(_ENGINE_CLASS_MAPPING.get(name))

    def get_engine(self, name=_BLANK):
        return self._engines[name]['engine']

    def get_all_engines(self):
        return [x['engine'] for x in self._engines.values()]

    def drop_engine(self, name=_BLANK):
        engine = self.get_engine(name)
        engine.dispose()
        del self._engines[name]

    def prepare_deferred(self, class_):
        if class_ is None:
            return
        if issubclass(class_, sqlalchemy.ext.declarative.DeferredReflection):
            class_.prepare(self.get_engine(class_._engine_name))

    def create_all(self, engine_name=_BLANK):
        """Create all tables etc. for an engine."""
        engine = self._engines[engine_name]
        _ENGINE_CLASS_MAPPING[engine_name].metadata.create_all(
            engine['engine'])

        # mark the database to be in the latest revision
        location = engine['alembic_location']
        if location:
            with alembic_context(engine['engine'], location) as ac:
                ac.migration_context._update_current_rev(
                    ac.migration_context.get_current_revision(),
                    ac.script.get_current_head())

    def _verify_engine(self, engine):
        # Step 1: Try to identify a testing table
        conn = engine.connect()
        try:
            conn.execute("SELECT * FROM tmp_functest")
        except sqlalchemy.exc.ProgrammingError:
            db_is_testing = False
        else:
            db_is_testing = True
        conn.invalidate()

        if (self.testing and db_is_testing):
            # We're running as a test and it is a test dabase. Continue
            return
        if (not self.testing and not db_is_testing):
            # We're running as a production system and we have a production
            # database. Continue.
            return

        # We're not in a valid state. Bail out.
        raise SystemExit("Not working against correct database (live vs "
                         "testing). Refusing to set up database connection "
                         "to {}.".format(engine.url))

    def assert_database_revision_is_current(self, engine_name=_BLANK):
        engine = self._engines[engine_name]
        location = engine['alembic_location']
        if not location:
            return
        with alembic_context(engine['engine'], location) as ac:
            head = ac.script.get_current_head()
            db_rev = ac.migration_context.get_current_revision()
            if head != db_rev:
                raise ValueError(
                    'Database revision {} of engine "{}" does not match '
                    'current revision {}.\nMaybe you want to call '
                    '`bin/alembic upgrade head`.'.format(
                        db_rev, engine_name, head))

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

    def empty(self, engine, table_names=None):
        transaction.abort()
        if table_names is None:
            inspector = sqlalchemy.engine.reflection.Inspector.from_engine(
                engine)
            table_names = inspector.get_table_names()
        if not table_names:
            return
        tables = ', '.join('"%s"' % x for x in table_names)
        self.session.execute('TRUNCATE %s RESTART IDENTITY' % tables,
                             bind=engine)
        zope.sqlalchemy.mark_changed(self.session)
        transaction.commit()


class alembic_context(object):

    def __init__(self, engine, script_location):
        self.engine = engine
        self.script_location = script_location

    def __enter__(self):
        self.conn = conn = self.engine.connect()
        return AlembicContext(conn, self.script_location)

    def __exit__(self, exc_type, exc_value, tb):
        self.conn.close()
        if exc_type is not None:
            raise exc_type(exc_value)


class AlembicContext(object):

    def __init__(self, conn, script_location):
        config = alembic.config.Config()
        config.set_main_option('script_location', script_location)
        self.migration_context = (
            alembic.migration.MigrationContext.configure(conn))
        self.script = alembic.script.ScriptDirectory.from_config(config)
