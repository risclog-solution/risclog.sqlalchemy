import pytest
import sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, String

from .. import model
from ..cache import ModelCache, MultipleObjectsFoundException


class TestObject(model.ObjectBase):
    _engine_name = 'db3'


Object = model.declarative_base(TestObject)


class PlainModel(Object):
    id = Column(String(10), primary_key=True)
    titel = Column(String(100))


class LinkedModel(Object):
    id = Column(String(10), primary_key=True)
    sequence_model_id = Column(
        Integer,
        ForeignKey('sequencemodel.id'),
        primary_key=True,
    )
    sequence_model = sqlalchemy.orm.relation('SequenceModel', uselist=False)


class SequenceModel(Object):
    id = Column(Integer, autoincrement=True, primary_key=True)
    titel = Column(String)


@pytest.fixture(scope='session')
def db(database_3):
    database_3.create_all('db3')
    yield database_3


def __create_cache(db, extra_settings=None):
    MODEL_SAVE_ORDER = [
        'PlainModel',
        'LinkedModel',
        'SequenceModel',
    ]
    MODEL_SEQUENCES = {
        'Model1': (('id', 'sequencemodel_id_seq'),),
    }
    settings = {
        'save_order': MODEL_SAVE_ORDER,
        'sequences': MODEL_SEQUENCES,
        'session': db.session,
        'engine_name': 'db3',
    }
    if extra_settings is not None:
        settings.update(extra_settings)
    cache = ModelCache(**settings)
    return cache


@pytest.fixture(scope='function')
def cache(db):
    yield __create_cache(db)


@pytest.fixture(scope='function')
def copy_cache(db):
    yield __create_cache(db, {'use_copy': True})


class TestFindGet:
    def test_find_uncached_object(self, cache):
        svg = PlainModel.create(
            id='1',
        )

        assert svg == cache.get(
            PlainModel,
            id=svg.id,
        )
        assert (
            svg
            == cache.find(
                PlainModel,
                id=svg.id,
            )[0]
        )

    def test_find_cached_object(self, cache):
        svg = cache.create(PlainModel, id='1')

        assert svg == cache.get(
            PlainModel,
            id=svg.id,
        )
        assert (
            svg
            == cache.find(
                PlainModel,
                id=svg.id,
            )[0]
        )

    def test_find_multiple_objects(self, cache):
        svg1 = PlainModel.create(id='1', titel='')
        svg2 = PlainModel.create(id='2', titel='')

        result = cache.find(PlainModel, titel='')

        assert 2 == len(result)
        assert svg1 in result
        assert svg2 in result

    def test_get_multiple_objects(self, cache):
        PlainModel.create(id='1', titel='')
        PlainModel.create(id='2', titel='')

        with pytest.raises(MultipleObjectsFoundException):
            cache.get(PlainModel, titel='')

    def test_non_existent_object(self, cache):
        PlainModel.create(
            id='1',
        )
        cache.create(
            PlainModel,
            id='2',
        )

        assert None is cache.get(
            PlainModel,
            id='3',
        )
        assert [] == cache.find(
            PlainModel,
            id='3',
        )

    def test_attribute_update(self, cache):
        svg = cache.create(PlainModel, id='1')
        cache.get(
            PlainModel,
            id=svg.id,
        )

        svg.id = '2'

        assert svg == cache.get(
            PlainModel,
            id=svg.id,
        )
        assert (
            svg
            == cache.find(
                PlainModel,
                id=svg.id,
            )[0]
        )


class TestCreate:
    def test_create_object(self, db, cache):
        cache.create(
            PlainModel,
            id='1',
        )
        cache.save_changes(db.session)

        assert 1 == PlainModel.query().count()

    def test_create_object_with_copy(self, db, copy_cache):
        copy_cache.create(
            PlainModel,
            id='1',
        )
        copy_cache.save_changes(db.session)

        assert 1 == PlainModel.query().count()


class TestFlush:
    def test_creation(self, db, cache):
        svg = cache.create(
            PlainModel,
            id='1',
        )
        cache.save_changes(db.session)

        assert 1 == PlainModel.query().filter(PlainModel.id == svg.id).count()

    def test_creation_with_copy(self, db, copy_cache):
        svg = copy_cache.create(
            PlainModel,
            id='1',
        )
        copy_cache.save_changes(db.session)

        assert 1 == PlainModel.query().filter(PlainModel.id == svg.id).count()

    def test_update(self, db, cache):
        old_id, new_id = '1', '42'
        PlainModel.create(
            id=old_id,
        )
        svg = cache.get(
            PlainModel,
            id=old_id,
        )

        svg.id = new_id
        cache.save_changes(db.session)

        assert 0 == PlainModel.query().filter(PlainModel.id == old_id).count()
        assert 1 == PlainModel.query().filter(PlainModel.id == new_id).count()

    def test_sequence_set_if_missing(self, db, cache):
        cache.create(
            SequenceModel,
            id=None,
        )
        cache.save_changes(db.session)
        wkz = SequenceModel.query().one()

        assert None is not wkz.id

    def test_existing_sequence_ignored(self, db, cache):
        id = 42
        cache.create(
            SequenceModel,
            id=id,
        )
        cache.save_changes(db.session)
        wkz = SequenceModel.query().one()

        assert id == wkz.id

    def test_synced_relationships(self, db, cache):
        sequence_model = SequenceModel.create()
        cache.create(LinkedModel, id='1', sequence_model=sequence_model)
        cache.save_changes(db.session)
        partner = LinkedModel.query().one()

        assert sequence_model == partner.sequence_model
        assert sequence_model.id == partner.sequence_model_id


class TestIndex:
    def test_find_populates_indices(self, cache):
        svg = PlainModel.create(
            id='1',
        )
        cache.find(
            PlainModel,
            id=svg.id,
        )
        cache.find(PlainModel, id=svg.id, titel='')

        assert [svg] == cache._cached_instances['PlainModel']
        assert [svg] == cache._indices['PlainModel'][('id',)][(svg.id,)]
        assert [svg] == cache._indices['PlainModel'][('id', 'titel')][
            (svg.id, svg.titel)
        ]

    def test_get_populates_indices(self, cache):
        svg = PlainModel.create(
            id='1',
        )
        cache.get(
            PlainModel,
            id=svg.id,
        )
        cache.get(PlainModel, id=svg.id, titel='')

        assert [svg] == cache._cached_instances['PlainModel']
        assert [svg] == cache._indices['PlainModel'][('id',)][(svg.id,)]
        assert [svg] == cache._indices['PlainModel'][('id', 'titel')][
            (svg.id, svg.titel)
        ]

    def test_attribute_changes_update_indices(self, cache):
        old_id, new_id = '1', '2'
        svg = PlainModel.create(
            id=old_id,
        )
        cache.get(
            PlainModel,
            id=svg.id,
        )

        svg.id = new_id

        assert [svg] == cache._cached_instances['PlainModel']
        assert [svg] == cache._indices['PlainModel'][('id',)][(new_id,)]
        assert (old_id,) not in cache._indices['PlainModel'][('id',)]

    def test_attribute_changes_update_indices2(self, cache):
        old_titel, new_titel = 'Old', 'New'
        svg1 = PlainModel.create(id='1', titel=old_titel)
        svg2 = PlainModel.create(id='2', titel=old_titel)
        cache.find(
            PlainModel,
            titel=old_titel,
        )

        svg1.titel = new_titel

        assert [svg1, svg2] == cache._cached_instances['PlainModel']
        assert [svg1] == cache._indices['PlainModel'][('titel',)][(new_titel,)]
        assert [svg2] == cache._indices['PlainModel'][('titel',)][(old_titel,)]
