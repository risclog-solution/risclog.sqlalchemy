from unittest import mock

import pkg_resources
import pytest
import risclog.sqlalchemy.model
import sqlalchemy
import transaction
from sqlalchemy import Column, Integer, String

from ..db import _ENGINE_CLASS_MAPPING, Database, get_database, register_class
from ..model import ObjectBase, declarative_base


def test_register_class_bails_when_registering_same_name_again():
    class Dummy:
        _engine_name = 'foobar'

    class Dummy2:
        _engine_name = 'foobar'

    with mock.patch.dict(_ENGINE_CLASS_MAPPING):
        register_class(Dummy)
        with pytest.raises(AssertionError) as err:
            register_class(Dummy2)
        assert (
            str(err.value)
            == 'An engine for name `foobar` is already registered.'
        )


def test_Database_is_able_to_handle_multiple_databases(
    database_1, database_2, request
):
    class ObjectBase_1(ObjectBase):
        _engine_name = 'db1'

    Base_1 = declarative_base(ObjectBase_1)

    class Model_1(Base_1):
        id = Column(Integer, primary_key=True)

    class ObjectBase_2(ObjectBase):
        _engine_name = 'db2'

    Base_2 = declarative_base(ObjectBase_2)

    class Model_2(Base_2):
        id = Column(Integer, primary_key=True)

    def tearDown():
        for class_ in [ObjectBase_1, ObjectBase_2]:
            risclog.sqlalchemy.db.unregister_class(class_)

    request.addfinalizer(tearDown)

    database_1.create_all('db1')
    database_1.create_all('db2')

    # Tables are stored in different databases:
    inspector_1 = sqlalchemy.inspect(database_1.get_engine('db1'))
    assert {'tmp_functest', 'model_1'} == set(inspector_1.get_table_names())

    inspector_2 = sqlalchemy.inspect(database_2.get_engine('db2'))
    assert {'tmp_functest', 'model_2'} == set(inspector_2.get_table_names())


def test_Database_cannot_be_created_twice(database_1):
    # The first time Database is created in fixture:
    with pytest.raises(AssertionError) as err:
        Database()
    assert str(err.value).startswith('Cannot create Database twice')


def test__verify_engine_checks_whether_the_correct_database_is_accessed(
    database_1,
):
    database_1.testing = False
    try:
        with pytest.raises(SystemExit) as err:
            database_1._verify_engine(database_1.get_engine('db1'))
    finally:
        database_1.testing = True
    assert str(err.value).startswith(
        'Not working against correct database (live vs testing).'
    )


def test_register_engine_bails_when_registering_an_engine_for_an_existing_name(
    database_1,
):
    with pytest.raises(AssertionError) as err:
        database_1.register_engine('<dsn>', name='db1')
    assert str(err.value) == 'An engine for name `db1` is already registered.'


def test_get_database_returns_database_utility(database_1):
    db = get_database(testing=True)
    assert isinstance(db, Database)


def test_get_database_makes_sure_testing_matches(database_1):
    with pytest.raises(AssertionError) as err:
        # In tests utility is set up with `testing=True`:
        get_database(testing=False)
    assert (
        str(err.value) == 'Requested testing status `False` does not '
        'match Database.testing.'
    )


def test_assert_db_rev_raises_if_mismatch(database_1):
    database_1._engines['db1'][
        'alembic_location'
    ] = pkg_resources.resource_filename(__name__, 'fixtures/alembic')
    with pytest.raises(ValueError):
        database_1.assert_database_revision_is_current('db1')


def test_database_is_detected_automatically_among_several(
    database_1, database_2, request
):
    class ObjectBase_1(ObjectBase):
        _engine_name = 'db1'

    Base_1 = declarative_base(ObjectBase_1)

    class Model_1(Base_1):
        id = Column(Integer, primary_key=True)

    class ObjectBase_2(ObjectBase):
        _engine_name = 'db2'

    Base_2 = declarative_base(ObjectBase_2)

    class Model_2(Base_2):
        id = Column(Integer, primary_key=True)

    def tearDown():
        risclog.sqlalchemy.db.unregister_class(Model_1)

    request.addfinalizer(tearDown)

    database_1.create_all('db1')
    database_2.create_all('db2')

    db = get_database(testing=True)
    # It used to be necessary to bind the session to the database to be
    # queried if more than one database was being used. This is no longer the
    # case as of SQLAlchemy 1.0.
    assert db.session.query(Model_1).count() == 0

    Model_1.create().persist()
    Model_2.create().persist()
    transaction.commit()

    # When using session.execute, a manual bind is necessary though
    with pytest.raises(RuntimeError):
        assert db.session.execute('SELECT count(*) FROM model_1').fetchall()
    # Using a bound session leads to a result:
    assert db.session.using_bind('db1').execute(
        'SELECT count(*) FROM model_1'
    ).fetchall() == [(1,)]


def test_create_all_marks_alembic_current(database_1, request):
    class TestObject(risclog.sqlalchemy.model.ObjectBase):
        _engine_name = 'db1'

    Object = risclog.sqlalchemy.model.declarative_base(TestObject)

    request.addfinalizer(
        lambda: risclog.sqlalchemy.db.unregister_class(Object)
    )

    database_1._engines['db1'][
        'alembic_location'
    ] = pkg_resources.resource_filename(__name__, 'fixtures/alembic')
    database_1.create_all('db1')
    database_1.assert_database_revision_is_current('db1')


def test_update_database_revision_to_current(database_1, request):
    class TestObject(risclog.sqlalchemy.model.ObjectBase):
        _engine_name = 'db1'

    Object = risclog.sqlalchemy.model.declarative_base(TestObject)

    request.addfinalizer(
        lambda: risclog.sqlalchemy.db.unregister_class(Object)
    )

    database_1._engines['db1'][
        'alembic_location'
    ] = pkg_resources.resource_filename(__name__, 'fixtures/alembic')
    with pytest.raises(ValueError):
        database_1.assert_database_revision_is_current('db1')
    database_1.update_database_revision_to_current('db1')
    database_1.assert_database_revision_is_current('db1')


def test_Model_query_can_take_args_for_memory_optimization(
    database_1, request
):
    class TestObject(risclog.sqlalchemy.model.ObjectBase):
        _engine_name = 'db1'

    Object = risclog.sqlalchemy.model.declarative_base(TestObject)

    request.addfinalizer(
        lambda: risclog.sqlalchemy.db.unregister_class(Object)
    )

    class TestObj(Object):
        id = Column(Integer, primary_key=True)
        column1 = Column(String)
        column2 = Column(String)

    database_1.create_all('db1')

    TestObj.create(column1='asdf', column2='bsdf').persist()

    obj = TestObj.query('column1').first()
    assert obj.column1 == 'asdf'
    with pytest.raises(AttributeError):
        obj.column2
