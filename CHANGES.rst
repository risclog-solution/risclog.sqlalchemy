=================================
Change log for risclog.sqlalchemy
=================================

7.1 (2024-03-22)
================

- Fix `sqlalchemy` 1.3 compatibility in `Database.empty()`.


7.0 (2024-03-21)
================

- Introduce new `RoutingSession` method `execute_with_bind()` to execute
  statements with a specific bind.
- `RoutingSession.using_bind()` is now deprecated and kept for backward
  compatibility.
  Instead of a new session instance, it now returns a shim that maps a
  minimal subset of session methods to the original session instance.
  This change was necessary because the previous implementation of creating
  a new session instance and copying all the original session's state
  proved unstable when used with SQLAlchemy 1.4. (One reason being the new
  autobegin feature of sessions changing interactions with `zope.sqlalchemy`.)


6.1 (2024-03-12)
================

- Add json encoder for `uuid.UUID` objects.

- Add `risclog.sqlalchemy.interfaces.Deleted` event which is fired when an
  object is deleted from the database.


6.0 (2023-09-26)
================

- Introduce `ModelCache` that reduces the number of DB requests when dealing
  with huge amounts of sqlalchemy models.

- Allow specifying `keep_session` and `expire_on_commit`.

- Drop support for Python 3.6.

- Drop support for SQLAlchemy 1.0 and 1.1.

- Add support for Python 3.10 and 3.11.

- Restrict supported SQLALchemy to < 2.


5.1 (2021-04-28)
================

Features
--------

- Ensure compatibility with ``SQLAlchemy >= 1.4``.

Other changes
-------------

- Use github actions as CI.


5.0 (2020-11-03)
================

Backward incompatible changes
-----------------------------

- Drop support for Python 2.

- Drop the ``python2`` extra in ``setup.py``.

Features
--------

- No longer constraint to ``zope.component < 4.4.1`` (introduced in 3.0).


4.0 (2020-02-17)
================

Backward incompatible changes
-----------------------------

- Add support for ``zope.sqlalchemy >= 1.3`` by requiring at least this version.
  (Older versions only supported ``zope.sqlalchemy <= 1.2``.)

- Drop support for PyPy, PyPy3, Python 3.4 and 3.5.

Other changes
-------------

- Add support for Python 3.7, 3.8, 3.9a3.

- Migrate to Github.


3.0 (2018-01-16)
================

- Drop support for Python 3.3.

- Reintroduce `RoutingSession.using_bind` as it is needed for executing queries
  in multi database environments. It was removed in version `2.0`.

- Pin to ``zope.component < 4.4.1`` for now as we are using a private variable
  from this package which has been removed lately.


2.3 (2017-04-06)
================

- Add the fixture ``.fixtures.database__selenium_testing`` to switch SQLAlchemy
  session handling to into the same way the live server does it. Using this
  fixture leads to `DetachedInstanceError` exceptions when using a database
  object after the commit. It has to be fetched again from the database.

- Omit files from sdist which are related to buildout, testing or mercurial.

2.2 (2017-01-12)
================

- Support Python 3.6 and PyPy3.

- Fix `setup.py` to no longer use absolute paths.


2.1 (2016-01-25)
================

- Add compatibility to `pypy`.

  Also removed explicit dependency to `psycopg2` as it's a PostgreSQL specific
  dependency and not compatible with pypy. You will need `psycopg2cffi` in
  order to run `risclog.sqlalchemy` with `pypy`.


2.0 (2015-12-18)
================

- Removed ``RoutingSession.using_bind``, require SQLAlchemy >= 1.0. (#13968)

- Updated API calls to alembic, require alembic >= 0.7. (#13968)

- Added documentation. (#13952)


1.8 (2015-09-29)
================

- Officially supporting Python 3.3 up to 3.5.

- Set maximum supported version numbers of ``alembic`` and ``SQLALchemy``
  in `setup.py`


1.7.1 (2014-10-15)
==================

- Fix bug in testing mode detection so it works with sqlite, too.


1.7 (2014-07-29)
================

- Have ``.model.Object.create`` use the ``**kw`` constructor instead of
  performing setattr itself.

- Made commit in db.empty optional.


1.6 (2014-06-23)
================

- Make test setup/teardown a bit more independent from the IDatabase utility.
- Made pyramid dependent code optional, because it is an optional requirement.


1.5.1 (2014-03-31)
==================

- Moved the project to bitbucket.org and prepared for public release.


1.5 (2014-03-06)
================

- Adjust test dependency for external projects, so pyramid is not required.
  (#1458)


1.4 (2014-01-27)
================

- Do not truncate `spatial_ref_sys` when emptying entire database. (#13144)


1.3 (2013-12-18)
================

- Do not truncate `alembic_versions` when emptying entire database (using
  `db.empty(engine)`)

- Fix create_defaults, so it can be used with multiple engines. (#1172)


1.2 (2013-12-13)
================

- Fixed setup.py


1.1 (2013-12-13)
================

- Allow ``.db.Database.empty()`` to not restart sequences. (This can be
  necassary if the user is not allowed to call `ALTER SEQUENCE`.)

- Create factory for JSON renderer, so it can be customized via arguments.
  (#1037)


1.0 (2013-12-11)
================

- CAUTION: Backward incompatible changes to provide multiple database
  support. You need to change:

  * Use the ``pyramid`` extra to use the pyramid serializers and call
    ``.serializer.patch()`` by yourself.

  * Changes in `.model`:

    + Use `.model.declarative_base(cls)` to register a class as SQLALchemy
      ``declarative_base``.

    + Use your own declarative_base as `.model.Object` has been dropped.

    + Create your own `ReflectedObject` as `.model.ReflectedObject` has been
      dropped.

  * Changes in `.db.Database`:

    + To get an instance use `.db.get_database(testing=<True|False>)`.

    + To register a database with the utility use ``register_engine``.

    + ``empty`` now expects to get the engine as first argument and allows to
      cadcade via (``cascade=True``).


    + ``_verify`` was removed, use ``_verify_engine`` now.

    + ``setup_utility`` was removed, it is now done in ``__init__``.

    + To access former ``engine``` attribute use ``get_engine``.

    + ``close`` was renamed to ``drop_engine``.

    + To create all tables for a database use ``create_all``.

  * Changes in `.testing`:

    + ``setUpDB`` lost its first argument as it was not used.

    + ``setUp`` now expects a dict or ``None``, see its docstring.

- Provide a way to insert default values for new created models. (#1137)

- Added support for schema migrations with alembic.

- Dropped support for `Python 2.6`.

- Added convenience functions to create `py.test` database fixtures.

- Declared `pyramid` as test dependency so tests only need the ``test``
  extra.

- Declared testing dependency on `plone.testing[test]` since we use
  `plone.testing.zca` which imports that ``test`` extra's dependencies.


0.6 (2013-06-27)
================

- Added convenience methods on `.db.Database` for teardown in tests.

- Updated to Buildout 2.

- Using py.test as testrunner.

- Added Python 3.3 compatibility.


0.5 (2013-06-14)
================

- Add Database methods for setting up a database utility and emptying tables.

- Add testing layer that sets up a database utility (requires plone.testing).


0.4 (2013-06-07)
================

- Add helper to provide transparent json encoding of sqlalchemy mapped objects,
  dates, datetimes and decimals. (#39)

- Add `create_defaults` class method on base model which can be used to create
  test data into the database.


0.3 (2013-06-04)
================

- Repair db setup for reflected and unreflected objects.


0.2 (2013-06-04)
================

- Add unreflected Object model next to the reflected Object model.


0.1 (2013-06-03)
================

initial release
