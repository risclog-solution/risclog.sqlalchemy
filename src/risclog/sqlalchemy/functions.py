from sqlalchemy.sql.expression import between, or_, and_


def in_interval(point, left, right):
    return or_(between(point, left, right),
               and_(point >= left, right == None))
