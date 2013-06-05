from risclog.sqlalchemy.interfaces import IDatabase, Added
import json
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import zope.component
import zope.interface
import zope.sqlalchemy
import risclog.sqlalchemy.serializer


class ObjectBase(object):

    @sqlalchemy.ext.declarative.declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @classmethod
    def create(cls, **kw):
        """Canonical way to create an object of this class."""
        obj = cls()
        for key, value in kw.items():
            if key not in dir(cls):
                raise KeyError('%r is not known on the class. Typo?' % key)
            setattr(obj, key, value)
        obj.persist()
        return obj

    def __json__(self, request):
        """Returns json serializable representation of this object."""
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
            cls.prepare(db.engine)


ReflectedObject = sqlalchemy.ext.declarative.declarative_base(
    cls=ReflectedObjectBase, metaclass=EnsureDeferredReflection)


Object = sqlalchemy.ext.declarative.declarative_base(cls=ObjectBase)
