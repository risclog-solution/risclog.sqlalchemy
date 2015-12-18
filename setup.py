# This should be only one line. If it must be multi-line, indent the second
# line onwards to keep the PKG-INFO file format intact.
"""Encapsulate sqlalchemy modelling infrastructure.
"""

from setuptools import setup, find_packages
import glob
import os.path


def project_path(*names):
    return os.path.join(os.path.dirname(__file__), *names)


setup(
    name='risclog.sqlalchemy',
    version='2.0',

    install_requires=[
        'SQLAlchemy >= 1.0',
        'alembic >= 0.7',
        'psycopg2',
        'pytz',
        'setuptools',
        'zope.component >= 4.0.1',
        'zope.interface',
        'zope.sqlalchemy',
    ],

    extras_require={
        'test': [
            'gocept.testdb',
        ],
        'self-test': [
            'mock',
            'pyramid',
            'pytest',
        ],
        'python2': [
            'plone.testing[test]'
        ],
        'pyramid': [
            'pyramid'
        ],
    },

    entry_points={},

    author='gocept <mail@gocept.com>',
    author_email='mail@gocept.com',
    license='ZPL 2.1',
    url='https://bitbucket.org/gocept/risclog.sqlalchemy/',

    keywords='sqlalchemy alembic model infrastructure utility',
    classifiers="""\
Development Status :: 5 - Production/Stable
Framework :: Pyramid
Intended Audience :: Developers
License :: OSI Approved
License :: OSI Approved :: Zope Public License
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: Implementation
Programming Language :: Python :: Implementation :: CPython
Topic :: Database
Topic :: Software Development :: Libraries
Topic :: Software Development :: Libraries :: Python Modules
"""[:-1].split('\n'),
    description=__doc__.strip(),
    long_description=(
        open('README.txt').read() +
        '\n\n' +
        open('HACKING.txt').read() +
        '\n\n' +
        open('CHANGES.txt').read()),
    namespace_packages=['risclog'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    data_files=[('', glob.glob(project_path('*.txt')))],
    zip_safe=False,
)
