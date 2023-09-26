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


Running tests
=============

Simply run `./pytest` in the root of the repository.


Documentation
=============

In order to build the Sphinx documentation, run the following command with a
python, where ``sphinx`` is installed::

    $ python setup.py build_sphinx


In order to upload the Sphinx documentation, run the following command with a
python, where ``sphinx-pypi-upload`` is installed::

    $ python setup.py upload_sphinx
