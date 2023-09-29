from sqlalchemy.sql.expression import and_, between, or_


def in_interval(point, left, right):
    return or_(
        between(point, left, right),
        and_(point >= left, right == None),  # noqa: E711 comparison to None
    )
