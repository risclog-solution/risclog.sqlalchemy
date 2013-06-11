import plone.testing
import plone.testing.zca
import risclog.sqlalchemy.db
import sqlalchemy
import transaction
import zope.component


class DatabaseLayer(plone.testing.Layer):

    defaultBases = [plone.testing.zca.LAYER_CLEANUP]

    def __init__(self, name, factory, managed_tables=None):
        super(DatabaseLayer, self).__init__()
        self._db_name = name
        self._db_factory = factory
        self._db_managed_tables = managed_tables

    def setUp(self):
        plone.testing.zca.pushGlobalRegistry()

        self[self._db_name] = db = self._db_factory()
        if db.exists:
            raise ValueError(
                'Database {}@{} already exists!'.format(
                    db.db_name, db.db_host))
        db.create()
        self.db_util = risclog.sqlalchemy.db.Database(db.dsn, testing=True)
        zope.component.provideUtility(self.db_util)

    def tearDown(self):
        # close all connections, but...
        transaction.abort()
        # ...sometimes transaction.abort() is not enough, and...
        db = zope.component.getUtility(risclog.sqlalchemy.interfaces.IDatabase)
        db.engine.dispose()
        # ...connections that have been checked-out from the pool and not yet
        # returned are not closed by dispose, either, so we have to hunt them
        # down ourselves:
        for conn in sqlalchemy.pool._refs:
            conn.close()

        self[self._db_name].drop()
        del self[self._db_name]

        plone.testing.zca.popGlobalRegistry()

    def testSetUp(self):
        self.db_util.empty(self._db_managed_tables)

    def testTearDown(self):
        self.db_util.session.close_all()
