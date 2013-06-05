import json
import sqlalchemy.orm
import logging

log = logging.getLogger(__name__)


#json encoder for sqlalchemy objects
def sqlalchemy_encode(o):
    columns = [c.key for c in sqlalchemy.orm.class_mapper(o.__class__).columns]
    result = dict((c, getattr(o, c)) for c in columns)
    return result


def patch():
    log.warn(u'Applying monkey patch: json '
             u'default encoder for sqlalchemy models.')
    json._default_encoder._default_orig = json._default_encoder.default
    json._default_encoder.default = sqlalchemy_encode
