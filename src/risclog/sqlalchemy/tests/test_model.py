import unittest

try:
    from unittest import mock
except ImportError:
    import mock


class ObjectBaseTests(unittest.TestCase):

    @mock.patch('risclog.sqlalchemy.serializer.sqlalchemy_encode')
    def test__json__calls_custom_serializer(self, sql_enc):
        import risclog.sqlalchemy.model
        model = risclog.sqlalchemy.model.ObjectBase()
        model.__json__({})
        sql_enc.assert_called_once_with(model)
