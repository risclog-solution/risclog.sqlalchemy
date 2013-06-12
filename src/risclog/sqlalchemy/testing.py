import risclog.sqlalchemy.db
import sqlalchemy
import transaction
import unittest
import zope.component


def setUpDB(name, factory):
    db = factory()
    if db.exists:
        raise ValueError(
            'Database {}@{} already exists!'.format(db.db_name, db.db_host))
    db.create()
    db_util = risclog.sqlalchemy.db.Database(db.dsn, testing=True)
    zope.component.provideUtility(db_util)
    return db


def tearDownDB(db):
    # close all connections, but...
    transaction.abort()
    # ...sometimes transaction.abort() is not enough, and...
    db_util = zope.component.getUtility(
        risclog.sqlalchemy.interfaces.IDatabase)
    db_util.engine.dispose()
    # ...connections that have been checked-out from the pool and not yet
    # returned are not closed by dispose, either, so we have to hunt them
    # down ourselves:
    for conn in sqlalchemy.pool._refs:
        conn.close()
    db.drop()


class TestCase(unittest.TestCase):

    def setUp(self, managed_tables=None):
        db_util = zope.component.getUtility(
            risclog.sqlalchemy.interfaces.IDatabase)
        db_util.empty(managed_tables)

    def tearDown(self):
        db_util = zope.component.getUtility(
            risclog.sqlalchemy.interfaces.IDatabase)
        db_util.session.close_all()
