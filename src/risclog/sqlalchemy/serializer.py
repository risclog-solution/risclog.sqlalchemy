from .model import ObjectBase
import datetime
import decimal
import json
import logging
import pyramid.renderers
import sqlalchemy.orm


log = logging.getLogger(__name__)


#json encoder for sqlalchemy objects
def sqlalchemy_encode(o):
    columns = [c.key for c in sqlalchemy.orm.class_mapper(o.__class__).columns]
    result = dict((c, getattr(o, c)) for c in columns)
    return result


def patch():
    log.info('Applying monkey patch: json '
             'default encoder for sqlalchemy models, datetime and decimal.')
    json._default_encoder._default_orig = json._default_encoder.default
    json._default_encoder.default = encode


def unpatch():
    log.info('Un-applying monkey patch: json '
             'default encoder for sqlalchemy models, datetime and decimal.')
    json._default_encoder.default = json._default_encoder._default_orig
    del json._default_encoder._default_orig


def datetime_encode(o, request=None):
    return o.isoformat()


def decimal_encode(o, request=None):
    return str(o)


ENCODERS = {ObjectBase: sqlalchemy_encode,
            datetime.date: datetime_encode,
            datetime.datetime: datetime_encode,
            decimal.Decimal: decimal_encode}


def encode(o):
    for klass, encoder in ENCODERS.items():
        if isinstance(o, klass):
            return encoder(o)
    return json._default_encoder._default_orig(o)


json_renderer = pyramid.renderers.JSON()
for klass, encoder in ENCODERS.items():
    json_renderer.add_adapter(klass, encoder)
