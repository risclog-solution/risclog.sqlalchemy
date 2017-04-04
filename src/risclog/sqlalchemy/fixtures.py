import risclog.sqlalchemy.db
import pytest


@pytest.fixture('function')
def database__selenium_testing(request):
    """Prepare the database for selenium testing:

    Remove the SQLAlchemy session after transaction.commit(). This is the same
    way as the live server does it. But this behavior might hinder the unit
    tests.
    """
    db = risclog.sqlalchemy.db.get_database(testing=True)
    extension = db.session_factory.session_factory.kw['extension']
    old_keep_session = extension.keep_session
    extension.keep_session = False

    def finalizer():
        extension.keep_session = old_keep_session

    request.addfinalizer(finalizer)
