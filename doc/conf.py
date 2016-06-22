# -*- coding: utf-8 -*-

import os
import sys

# Get the project root dir, which is the parent dir of this
cwd = os.getcwd()
project_root = os.path.dirname(cwd)

sys.path.insert(0, project_root)
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), "_ext")))

# package data
about = {}
with open("../tmuxp/__about__.py") as fp:
    exec(fp.read(), about)


extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.intersphinx',
              'sphinx.ext.todo',
              'aafig',
              'releases',
              ]

releases_unstable_prehistory = True
releases_document_name = "history"
releases_issue_uri = "https://github.com/tony/tmuxp/issues/%s"
releases_release_uri = "https://github.com/tony/tmuxp/tree/%s"

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = about['__title__']
copyright = about['__copyright__']

version = '%s' % ('.'.join(about['__version__'].split('.'))[:2])
release = '%s' % (about['__version__'])

exclude_patterns = ['_build']

pygments_style = 'sphinx'

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if on_rtd:
    html_theme = 'default'
else:
    try:
        import sphinx_rtd_theme
        html_theme = "sphinx_rtd_theme"
        html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
    except ImportError:
        html_theme = 'pyramid'

html_theme_path = ['_themes']
html_static_path = ['_static']

htmlhelp_basename = '%sdoc' % about['__title__']

latex_documents = [
    ('index', '{0}.tex'.format(about['__package_name__']),
     '{0} Documentation'.format(about['__title__']),
     about['__author__'], 'manual'),
]

man_pages = [
    ('index', about['__package_name__'],
     '{0} Documentation'.format(about['__title__']),
     about['__author__'], 1),
]

texinfo_documents = [
    ('index', '{0}'.format(about['__package_name__']),
     '{0} Documentation'.format(about['__title__']),
     about['__author__'], about['__package_name__'],
     about['__description__'], 'Miscellaneous'),
]

intersphinx_mapping = {
    'python': ('http://docs.python.org/', None),
    'libtmux': ('https://libtmux.readthedocs.io/', None)
}

# aafig format, try to get working with pdf
aafig_format = dict(latex='pdf', html='gif')

aafig_default_options = dict(
    scale=.75,
    aspect=0.5,
    proportional=True,
)
