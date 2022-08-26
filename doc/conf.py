import os
import sys

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('_themes'))
extensions = []

source_suffix = '.txt'
master_doc = 'index'
exclude_patterns = ['_build']

project = u'risclog.sqlalchemy'
copyright = u"""\
    2011 - 2017 Zope Foundation and Contributors.
    <a href="http://sphinx.pocoo.org/">Sphinx</a>-Theme adapted from
    <a href="http://jinja.pocoo.org/docs/">Jinja</a>
"""
version = '2.0'  # XXX determine automatically
release = version

pygments_style = 'sphinx'
