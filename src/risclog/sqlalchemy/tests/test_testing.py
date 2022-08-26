import gocept.testdb
import pkg_resources
import pytest
import sqlalchemy

from risclog.sqlalchemy.testing import database_fixture_factory

PREFIX = 'rl.sqla.testing-241177-'


@pytest.fixture(scope='session')
def database(request):
    schema_path = pkg_resources.resource_filename(
        'risclog.sqlalchemy.tests', 'fixtures/example-schema.sql')
    return database_fixture_factory(
        request,
        PREFIX + 'db',
        name='test_testing',
        schema_path=schema_path,
        template_db_name=PREFIX + 'template')


def test_testing__database_fixture_factory__1(database):
    """It creates a template database if a name is given."""
    db = gocept.testdb.PostgreSQL(prefix=PREFIX)
    template_db_dsn = db.get_dsn(PREFIX + 'template')
    dbs = sorted([x
                  for x in db.list_db_names()
                  if x.startswith(PREFIX)])
    assert PREFIX + 'template' in dbs
    assert len([x for x in dbs if x.startswith(PREFIX + 'db')]) >= 1

    def assert_db_content(dsn):
        engine = sqlalchemy.create_engine(dsn)
        conn = engine.connect()
        res = engine.execute('SELECT key FROM example')
        assert res.fetchall() == [(42, )]
        conn.invalidate()
        conn.close()

    assert_db_content(template_db_dsn)
    assert_db_content(database.get_engine('test_testing').url)
