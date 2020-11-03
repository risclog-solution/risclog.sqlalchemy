=============================
Developing risclog.sqlalchemy
=============================

:Author:
    `gocept <http://gocept.com/>`_ <mail@gocept.com>

:Outdated Online documentation:
    https://pythonhosted.org/risclog.sqlalchemy/

:PyPI page:
    https://pypi.org/project/risclog.sqlalchemy/

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
    py36 develop-inst-nodeps...
    ...
    py39 develop-inst-nodeps...

Documentation
=============

In order to build the Sphinx documentation, run the following command with a
python, where ``sphinx`` is installed::

    $ python setup.py build_sphinx


In order to upload the Sphinx documentation, run the following command with a
python, where ``sphinx-pypi-upload`` is installed::

    $ python setup.py upload_sphinx
