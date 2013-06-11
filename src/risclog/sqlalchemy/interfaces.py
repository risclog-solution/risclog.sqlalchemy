import zope.interface
import zope.interface.interfaces


class IDatabase(zope.interface.Interface):

    def setup_utility():
        """Register the database as a ZCA utility.

        Also verifies that the testing status of the database and this utility
        match.

        """

    def empty(table_names=None):
        """Truncate any tables passed, or all tables found in the db.

        """


class Added(zope.interface.interfaces.ObjectEvent):
    """An object has been created and added to the session."""

    def __init__(self, object):
        self.object = object
