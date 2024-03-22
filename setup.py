# This should be only one line. If it must be multi-line, indent the second
# line onwards to keep the PKG-INFO file format intact.
"""Encapsulate sqlalchemy modelling infrastructure.
"""

import glob

from setuptools import find_packages, setup

setup(
    name='risclog.sqlalchemy',
    version='7.1',
    python_requires='>=3.7',
    install_requires=[
        'SQLAlchemy >= 1.0, < 2',
        'alembic >= 0.7',
        'pytz',
        'setuptools',
        'transaction',
        'zope.component >= 4.0.1',
        'zope.interface',
        'zope.sqlalchemy >= 1.3',
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
        'pyramid': ['pyramid'],
    },
    entry_points={},
    author='gocept <mail@gocept.com>',
    author_email='mail@gocept.com',
    license='ZPL 2.1',
    url='https://github.com/gocept/risclog.sqlalchemy',
    keywords='sqlalchemy alembic model infrastructure utility',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'License :: OSI Approved',
        'License :: OSI Approved :: Zope Public License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    description=__doc__.strip(),
    long_description=(
        open('README.rst').read()
        + '\n\n'
        + open('HACKING.rst').read()
        + '\n\n'
        + open('CHANGES.rst').read()
    ),
    namespace_packages=['risclog'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    data_files=[('', glob.glob('*.rst'))],
    zip_safe=False,
)
