from risclog.sqlalchemy.db import register_class
from risclog.sqlalchemy.interfaces import IDatabase, Added
from zope.component._compat import _BLANK
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import zope.component
import zope.interface
import zope.sqlalchemy


class ObjectBase(object):

    _engine_name = _BLANK  # set another name to use multiple databases

    @sqlalchemy.ext.declarative.declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @classmethod
    def create(cls, **kw):
        """Canonical way to create an object of this class."""
        obj = cls(**kw)
        obj.persist()
        return obj

    @classmethod
    def find_or_create(cls, **kw):
        try:
            return cls.query().filter_by(**kw).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return cls.create(**kw)

    @classmethod
    def create_defaults(cls):
        """Overwrite in subclass to create example data of this model."""
        pass

    def __json__(self, request):
        """Returns json serializable representation of this object."""
        import risclog.sqlalchemy.serializer  # prevent circular import
        return risclog.sqlalchemy.serializer.sqlalchemy_encode(self)

    def persist(self):
        """Add make the newly created object known to the database."""
        zope.component.getUtility(IDatabase).add(self)
        zope.event.notify(Added(self))

    def delete(self):
        """Remove the object from the database."""
        zope.component.getUtility(IDatabase).delete(self)

    @classmethod
    def query(cls):
        return zope.component.getUtility(IDatabase).query(cls)

    @classmethod
    def get(cls, id):
        return cls.query().get(id)

    @classmethod
    def context_factory(cls, request):
        return cls.query().filter_by(**request.matchdict).first()


class ReflectedObjectBase(
        ObjectBase, sqlalchemy.ext.declarative.DeferredReflection):
    pass

# Reflection may (have to) happen before all model classes are imported. (We
# might import the whole model before doing reflection but we don't want to
# have to.) We therefore need to give each class another chance to do the
# reflection after it is constructed.


class EnsureDeferredReflection(sqlalchemy.ext.declarative.DeclarativeMeta):

    def __init__(cls, name, bases, dct):
        super(EnsureDeferredReflection, cls).__init__(name, bases, dct)
        db = zope.component.queryUtility(IDatabase)
        if db is not None:
            db.prepare_deferred(cls)


# To create your own ReflectedObject as declarative_base you may call:
# ReflectedObject = declarative_base(cls=ReflectedObjectBase,
#                                    metaclass=EnsureDeferredReflection)

# Enable your own class_registry by calling
# ObjectBase = declarative_base(ObjectBase, class_registry=class_registry)
# You will need this if you want to use `create_defaults` on a model.
class_registry = {}


def declarative_base(cls, **kw):
    """Create a `declarative_base` from a base Object."""
    obj = sqlalchemy.ext.declarative.declarative_base(cls=cls, **kw)
    register_class(obj)
    return obj
