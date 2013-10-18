from zope.component._compat import _BLANK
import gocept.testdb
import risclog.sqlalchemy.db
import sqlalchemy
import transaction
import unittest
import zope.component


def get_db_util():
    """Get the database utility registered with `name`."""
    return zope.component.queryUtility(
        risclog.sqlalchemy.interfaces.IDatabase)


def setUpDB(factory, name=_BLANK, alembic_location=None):
    db = factory()
    if db.exists:
        raise ValueError(
            'Database {}@{} already exists!'.format(db.db_name, db.db_host))
    db.create()
    db_util = risclog.sqlalchemy.db.get_database(testing=True)
    db_util.register_engine(
        db.dsn, name=name, alembic_location=alembic_location)
    return db


def tearDownDB(db, name=_BLANK):
    # close all connections, but...
    transaction.abort()
    # ...sometimes transaction.abort() is not enough, and...
    db_util = get_db_util()
    db_util.drop_engine(name)
    # ...connections that have been checked-out from the pool and not yet
    # returned are not closed by dispose, either, so we have to hunt them
    # down ourselves:
    for conn in sqlalchemy.pool._refs:
        conn.close()
    db.drop()
    if not db_util.get_all_engines():
        # Removed last database so we can drop the utility:
        db_util._teardown_utility()


def database_fixture_factory(prefix, name=_BLANK, schema_path=None,
                             create_all=False, alembic_location=None):
    """Factory creating a py.test fixture for a database.

    prefix  ... str to prefix name of created database
    name ... str name of database to support multiple databases
    schema_path ... load this schema into the created database
    create_all ... Create all tables etc. in database?
    alembic_location ... Path where alembic migration scripts live.

    Usage example::

        @pytest.yield_fixture
        @pytest.fixture(scope='session')
        def database():
            yield from database_fixture_factory('rl.<prefix>')

    """
    def db_factory():
        return gocept.testdb.PostgreSQL(
            prefix=prefix, schema_path=schema_path)


    db = setUpDB(db_factory, name, alembic_location)
    db_util = get_db_util()
    if create_all:
        db_util.create_all(name)
        transaction.commit()
    yield db_util
    tearDownDB(db, name)


def setUp(managed_tables=None):
    """Set up session for test.

    managed_tables ... if None: empty all table in all engines
                       if dict: key is engine name, value is list of tables
                                which should get emptyed.

    """
    db_util = get_db_util()
    if managed_tables is None:
        for engine in db_util.get_all_engines():
            db_util.empty(engine)
    else:
        for engine_name, tables in managed_tables.values():
            db_util.empty(engine, tables)


def tearDown():
    db_util = get_db_util()
    db_util.session.close_all()


def database_test_livecycle_fixture_factory():
    """Factory creating a py.test fixture for DB livecyle per test.

    Usage example::

        @pytest.yield_fixture
        @pytest.fixture(scope='function', autouse=True)
        def database_test_livecycle(database):
            yield from database_test_livecycle_fixture_factory()

    Caution: You need only one of these fixtures but it should depend on all
    databases you use.

    """
    risclog.sqlalchemy.testing.setUp()
    yield
    tearDown()


class TestCase(unittest.TestCase):

    def setUp(self, managed_tables=None):
        setUp(managed_tables)

    def tearDown(self):
        tearDown()
