import pytest
import risclog.sqlalchemy.testing
import risclog.sqlalchemy.serializer


@pytest.fixture(scope='session')
def database_1(request):
    return risclog.sqlalchemy.testing.database_fixture_factory(
        request, 'risclog.sqlalchemy.db1', 'db1')


@pytest.fixture(scope='session')
def database_2(request):
    return risclog.sqlalchemy.testing.database_fixture_factory(
        request, 'risclog.sqlalchemy.db2', 'db2')


@pytest.fixture(scope='function', autouse=True)
def database_test_livecycle(request, database_1, database_2):
    """Make sure each test gets a clean database + session."""
    return risclog.sqlalchemy.testing.database_test_livecycle_fixture_factory(
        request)


@pytest.fixture(scope='class')
def patched_serializer(request):
    """Patch pyramid serializer to be able to serialize Decimal and Datetime."""
    risclog.sqlalchemy.serializer.patch()
    request.addfinalizer(risclog.sqlalchemy.serializer.unpatch)


@pytest.fixture(scope='function')
def test_model(request):
    """Create testmodel for test_serializer."""
    from sqlalchemy import Column, Text
    import risclog.sqlalchemy.model

    class TestObject(risclog.sqlalchemy.model.ObjectBase):
        _engine_name = 'test_serializer'

    Object = risclog.sqlalchemy.model.declarative_base(TestObject)

    class ExampleModel(Object):
        __tablename__ = 'foo'
        foo = Column(Text, primary_key=True)

    def unregister_model():
        risclog.sqlalchemy.db.unregister_class(Object)

    test_object = ExampleModel()
    test_object.foo = u'bar'
    request.addfinalizer(unregister_model)
    return test_object
