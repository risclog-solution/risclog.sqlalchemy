from zope.component._compat import _BLANK
import zope.interface
import zope.interface.interfaces


class IDatabase(zope.interface.Interface):
    """Utility which is able to coordinate the access to multiple databases."""

    def register_engine(dsn, engine_args={}, name=_BLANK):
        """Register a new engine with the database utility."""

    def get_engine(name=_BLANK):
        """Get a registered engine by its name."""

    def setup_utility():
        """Register the database as a ZCA utility.

        Also verifies that the testing status of the database and this utility
        match.
        """

    def query(*args, **kw):
        """Query the session."""

    def empty(engine, table_names=None):
        """Truncate any tables passed, or all tables found in the engine."""


class Added(zope.interface.interfaces.ObjectEvent):
    """An object has been created and added to the session."""

    def __init__(self, object):
        self.object = object
