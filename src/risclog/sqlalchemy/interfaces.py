import zope.interface
import zope.interface.interfaces


class IDatabase(zope.interface.Interface):
    pass


class Added(zope.interface.interfaces.ObjectEvent):
    """An object has been created and added to the session."""

    def __init__(self, object):
        self.object = object
