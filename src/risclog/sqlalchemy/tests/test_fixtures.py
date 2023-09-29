import pytest
import risclog.sqlalchemy.db
import risclog.sqlalchemy.testing
import sqlalchemy.orm.exc
import transaction

pytest_plugins = 'risclog.sqlalchemy.fixtures'


@pytest.fixture(scope='function')
def example_model(test_model_factory):
    """Create a persisted example object in the database."""
    model = test_model_factory('db1')
    db = risclog.sqlalchemy.db.get_database(testing=True)
    db.create_all('db1')
    model.persist()
    transaction.commit()
    return model


def test_fixtures__database__selenium_testing__1(database_1, example_model):
    """It keeps the session by default after commit."""
    assert example_model.foo == 'bar'


def test_fixtures__database__selenium_testing__2(
    database_1, database__selenium_testing, example_model
):
    """It removes the session if database__selenium_testing is used ."""
    with pytest.raises(sqlalchemy.orm.exc.DetachedInstanceError):
        example_model.foo = 'bar'
