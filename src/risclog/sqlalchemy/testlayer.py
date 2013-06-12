import plone.testing
import plone.testing.zca
import risclog.sqlalchemy.testing


class DatabaseLayer(plone.testing.Layer):

    defaultBases = [plone.testing.zca.LAYER_CLEANUP]

    def __init__(self, name, factory, managed_tables=None):
        super(DatabaseLayer, self).__init__()
        self._db_name = name
        self._db_factory = factory
        self._db_managed_tables = managed_tables

    def setUp(self):
        plone.testing.zca.pushGlobalRegistry()
        self[self._db_name] = risclog.sqlalchemy.testing.setUpDB(
            self._db_name, self._db_factory)

    def tearDown(self):
        risclog.sqlalchemy.testing.tearDownDB(self[self._db_name])
        del self[self._db_name]
        plone.testing.zca.popGlobalRegistry()

    def testSetUp(self):
        risclog.sqlalchemy.testing.setUp(self._db_managed_tables)

    def testTearDown(self):
        risclog.sqlalchemy.testing.tearDown()
