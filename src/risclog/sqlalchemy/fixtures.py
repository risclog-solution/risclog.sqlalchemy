import pytest
import risclog.sqlalchemy.db


@pytest.fixture(scope='function')
def database__selenium_testing():
    """Prepare the database for selenium testing:

    Remove the SQLAlchemy session after transaction.commit(). This is the same
    way as the live server does it. But this behavior might hinder the unit
    tests.
    """
    db = risclog.sqlalchemy.db.get_database(testing=True)
    old_keep_session = db.zope_transaction_events.keep_session
    db.zope_transaction_events.keep_session = False

    yield
    db.zope_transaction_events.keep_session = old_keep_session
