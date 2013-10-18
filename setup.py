# Copyright (c) 2013 gocept gmbh & co. kg
# See also LICENSE.txt

# This should be only one line. If it must be multi-line, indent the second
# line onwards to keep the PKG-INFO file format intact.
"""Encapsulate sqlalchemy functions for risclog projects.
"""

from setuptools import setup, find_packages
import glob
import os.path


def project_path(*names):
    return os.path.join(os.path.dirname(__file__), *names)


setup(
    name='risclog.sqlalchemy',
    version='1.0.dev0',

    install_requires=[
        'SQLAlchemy',
        'alembic',
        'psycopg2',
        'pytz',
        'setuptools',
        'zope.component',
        'zope.interface',
        'zope.sqlalchemy',
    ],

    extras_require={
        'test': [
            'gocept.testdb',
            'mock',
            'pyramid',
            'pytest',
            'pytest-cache',
        ],
        'python2': ['plone.testing[test]'],
        'pyramid': ['pyramid'],
    },

    entry_points={},

    author='gocept <mail@gocept.com>',
    author_email='mail@gocept.com',
    license='ZPL 2.1',
    url='https://redmine.risclog.de/projects/risclog-sqlalchemy/',

    keywords='sqlalchemy risclog',
    classifiers="""\
License :: OSI Approved :: Zope Public License
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.3
"""[:-1].split('\n'),
    description=__doc__.strip(),
    long_description='\n\n'.join(open(project_path(name)).read() for name in (
        'README.txt',
        'HACKING.txt',
        'CHANGES.txt',
    )),

    namespace_packages=['risclog'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    data_files=[('', glob.glob(project_path('*.txt')))],
    zip_safe=False,
)
