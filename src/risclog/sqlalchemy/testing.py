from zope.component._compat import _BLANK
import gocept.testdb
import risclog.sqlalchemy.db
import sqlalchemy
import transaction
import unittest
import zope.component


def setUpDB(factory):
    db = factory()
    if db.exists:
        raise ValueError(
            'Database {}@{} already exists!'.format(db.db_name, db.db_host))
    db.create()
    db_util = risclog.sqlalchemy.db.Database(db.dsn, testing=True)
    db_util.setup_utility()
    return db


def get_db_util():
    """Get the database utility registered with `name`."""
    return zope.component.getUtility(
        risclog.sqlalchemy.interfaces.IDatabase)


def tearDownDB(db):
    # close all connections, but...
    transaction.abort()
    # ...sometimes transaction.abort() is not enough, and...
    db_util = get_db_util()
    db_util.engine.dispose()
    # ...connections that have been checked-out from the pool and not yet
    # returned are not closed by dispose, either, so we have to hunt them
    # down ourselves:
    for conn in sqlalchemy.pool._refs:
        conn.close()
    db.drop()
    db_util.teardown_utility()


def database_fixture_factory(request, prefix, schema_path=None):
    """Factory creating a py.test fixture for a database.

    request ... request fixture
    prefix  ... str to prefix name of created database
    schema_path ... load this schema into the created database

    Usage example::

        @pytest.fixture(scope='session')
        def database(request):
            return database_fixture_factory(request, 'rl.<prefix>')

    """
    def db_factory():
        return gocept.testdb.PostgreSQL(
            prefix=prefix, schema_path=schema_path)

    def dropdb():
        tearDownDB(db)

    db = setUpDB(db_factory)
    request.addfinalizer(dropdb)
    return get_db_util()


def setUp(managed_tables=None):
    db_util = get_db_util()
    db_util.empty(managed_tables)


def tearDown():
    db_util = get_db_util()
    db_util.session.close_all()


def database_test_livecycle_fixture_factory(request):
    """Factory creating a py.test fixture for DB livecyle per test.

    request ... request fixture

        Usage example::

        @pytest.fixture(scope='function', autouse=True)
        def database_session_livecycle(request, database):
            return database_test_livecycle_fixture_factory()

    """
    def tear_down():
        tearDown()

    risclog.sqlalchemy.testing.setUp()
    request.addfinalizer(tear_down)


class TestCase(unittest.TestCase):

    def setUp(self, managed_tables=None):
        setUp(managed_tables)

    def tearDown(self):
        tearDown()
