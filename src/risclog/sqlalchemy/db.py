import os
import risclog.sqlalchemy.interfaces
import risclog.sqlalchemy.model
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import zope.component
import zope.interface
import zope.sqlalchemy


class Database(object):

    zope.interface.implements(risclog.sqlalchemy.interfaces.IDatabase)

    def __init__(self, dsn, engine_args={}, testing=False):
        self.dsn = dsn
        self.testing = testing
        self._verify()
        engine_args['echo'] = bool(int(os.environ.get(
            'ECHO_SQLALCHEMY_QUERIES', '0')))
        self.engine = sqlalchemy.create_engine(dsn, **engine_args)
        self.session_factory = sqlalchemy.orm.scoped_session(
            sqlalchemy.orm.sessionmaker(
                bind=self.engine,
                extension=zope.sqlalchemy.ZopeTransactionExtension(
                    keep_session=testing)))
        # Some model classes may already have been constructed without having
        # had access to a db engine so far, so give them a chance to do the
        # reflection now. We might do this when publishing the database
        # utility but we don't want to have to.
        risclog.sqlalchemy.model.ReflectedObject.prepare(self.engine)

    def _verify(self):
        # Step 1: Try to identify a testing table
        engine = sqlalchemy.create_engine(self.dsn)
        conn = engine.connect()
        try:
            conn.execute("SELECT * FROM tmp_functest")
        except sqlalchemy.exc.ProgrammingError:
            db_is_testing = False
        else:
            db_is_testing = True
        conn.invalidate()

        if (self.testing and db_is_testing):
            # We're running as a test and it is a test dabase. Continue
            return
        if (not self.testing and not db_is_testing):
            # We're running as a production system and we have a production
            # database. Continue.
            return

        # We're not in a valid state. Bail out.
        raise SystemExit("Not working against correct database (live vs "
                         "testing). Refusing to set up database connection.")

    @property
    def session(self):
        return self.session_factory()

    def add(self, obj):
        return self.session.add(obj)

    def delete(self, obj):
        return self.session.delete(obj)

    def query(self, *args, **kw):
        return self.session.query(*args, **kw)

    def setup_utility(self):
        self._verify()
        zope.component.provideUtility(self)
