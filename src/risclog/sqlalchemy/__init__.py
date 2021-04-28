try:
    from psycopg2cffi import compat
except ImportError:
    pass
else:  # pragma: no cover
    compat.register()
    del compat
