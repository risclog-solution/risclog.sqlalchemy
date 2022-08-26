=============================
Developing risclog.sqlalchemy
=============================

:Author:
    `gocept <http://gocept.com/>`_ <mail@gocept.com>

:Online documentation:
    https://pythonhosted.org/risclog.sqlalchemy/

:PyPI page:
    http://pypi.python.org/pypi/risclog.sqlalchemy/

:Issue tracker:
    https://github.com/gocept/risclog.sqlalchemy/issues/

:Source code:
    https://github.com/gocept/risclog.sqlalchemy

:Current change log:
    https://github.com/gocept/risclog.sqlalchemy/blob/master/CHANGES.rst

Buildout configuration
======================

This package ships with a minimum buildout config which allows to run the
tests::

    $ python bootstrap.py
    $ bin/buildout
    $ bin/test

Using Tox
=========

``risclog.sqlalchemy`` ships with a tox configuration that allows to run all
tests against all supported python versions. You will need ``tox`` to run those
tests::

    $ tox
    py27 develop-inst-nodeps...
    ...
    py33 develop-inst-nodeps...


Using docker containers for the tests
=====================================

Prerequisites
+++++++++++++

* ``createdb`` has to be on $PATH.
* Run the follwing commands (you might change the passwords used)::

    docker run --name postgres96 -e POSTGRES_PASSWORD=j§V7iJY@1xTG67J@ -d -p 5433:5432 postgres:9.6
    echo "localhost:5433:*:postgres:j§V7iJY@1xTG67J@" >> ~/.pgpass
    chmod 600 ~/.pgpass

Run the tests
+++++++++++++

* POSTGRES_PORT=5433 POSTGRES_USER=postgres tox

Documentation
=============

In order to build the Sphinx documentation, run the following command with a
python, where ``sphinx`` is installed::

    $ python setup.py build_sphinx


In order to upload the Sphinx documentation, run the following command with a
python, where ``sphinx-pypi-upload`` is installed::

    $ python setup.py upload_sphinx
