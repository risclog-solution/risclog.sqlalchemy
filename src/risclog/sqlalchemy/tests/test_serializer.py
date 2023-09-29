import datetime
import decimal
import json

import pytest
import pytz
import risclog.sqlalchemy.serializer


@pytest.fixture(scope='function')
def test_model(test_model_factory):
    return test_model_factory('test_serializer')


def test_returns_json_serializable_data_of_sqlalchemy_object(test_model):
    result = risclog.sqlalchemy.serializer.sqlalchemy_encode(test_model)
    assert {'foo': 'bar'} == result


def test_returns_json_serializable_data_of_date_object():
    result = risclog.sqlalchemy.serializer.datetime_encode(
        datetime.date(2013, 6, 20)
    )
    assert '2013-06-20' == result


def test_returns_json_serializable_data_of_decimal_object():
    result = risclog.sqlalchemy.serializer.decimal_encode(
        decimal.Decimal('3500.17')
    )
    assert '3500.17' == result


def callJSONDumps(data):
    result = json.dumps(data)
    return json.loads(result)


@pytest.mark.usefixtures('patched_serializer')
def test_json_dumps_can_dump_sqlalchemy_objects(test_model):
    assert [{'foo': 'bar'}, {'foo': 'bar'}] == callJSONDumps(
        [test_model, test_model]
    )


def test_json_dumps_can_dump_dates_and_datetimes(patched_serializer):
    assert ['2013-06-20', '2013-06-20T09:55:12'] == callJSONDumps(
        [datetime.date(2013, 6, 20), datetime.datetime(2013, 6, 20, 9, 55, 12)]
    )
    assert '2013-06-20T09:55:12+00:00' == callJSONDumps(
        datetime.datetime(2013, 6, 20, 9, 55, 12, tzinfo=pytz.utc)
    )


def test_json_dumps_can_dump_decimals(patched_serializer):
    assert '12345.67' == callJSONDumps(decimal.Decimal('12345.67'))
