import pytest
import risclog.sqlalchemy.testing
import risclog.sqlalchemy.serializer


@pytest.yield_fixture
@pytest.fixture(scope='session')
def database_1():
    yield from risclog.sqlalchemy.testing.database_fixture_factory(
        'risclog.sqlalchemy.db1', 'db1')


@pytest.yield_fixture
@pytest.fixture(scope='session')
def database_2():
    yield from risclog.sqlalchemy.testing.database_fixture_factory(
        'risclog.sqlalchemy.db2', 'db2')


@pytest.yield_fixture
@pytest.fixture(scope='function', autouse=True)
def database_test_livecycle(database_1, database_2):
    """Make sure each test gets a clean database + session."""
    yield from (
        risclog.sqlalchemy.testing.database_test_livecycle_fixture_factory())


@pytest.yield_fixture
@pytest.fixture(scope='function')
def patched_serializer():
    """Patch pyramid serializer to be able to serialize Decimal and Datetime."""
    risclog.sqlalchemy.serializer.patch()
    yield
    risclog.sqlalchemy.serializer.unpatch()


@pytest.yield_fixture
@pytest.fixture(scope='function')
def test_model():
    """Create testmodel for test_serializer."""
    from sqlalchemy import Column, Text
    import risclog.sqlalchemy.model

    class TestObject(risclog.sqlalchemy.model.ObjectBase):
        _engine_name = 'test_serializer'

    Object = risclog.sqlalchemy.model.declarative_base(TestObject)

    class ExampleModel(Object):
        __tablename__ = 'foo'
        foo = Column(Text, primary_key=True)

    test_object = ExampleModel()
    test_object.foo = u'bar'
    yield test_object
    risclog.sqlalchemy.db.unregister_class(Object)
