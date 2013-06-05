from sqlalchemy import Column, Text
import json
import risclog.sqlalchemy.model
import risclog.sqlalchemy.serializer
import unittest


class TestModel(risclog.sqlalchemy.model.Object):
    foo = Column(Text, primary_key=True)

test_object = TestModel()
test_object.foo = u'bar'


class SQLAlchemyEncoderTest(unittest.TestCase):

    def test_returns_json_serializable_data_of_single_object(self):
        result = risclog.sqlalchemy.serializer.sqlalchemy_encode(test_object)
        self.assertEqual({'foo': u'bar'}, result)


class JSONDumpsMonkeyPatchTest(unittest.TestCase):

    def test_json_dumps_can_dump_sqlalchemy_objects(self):
        result = json.dumps([test_object, test_object])
        self.assertEqual([{'foo': u'bar'}, {'foo': u'bar'}],
                         json.loads(result))

