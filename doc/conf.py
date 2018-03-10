# -*- coding: utf-8 -*-

import os
import sys
import alagitpull


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


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'aafig',
    'releases',
    'alagitpull',
]

releases_unstable_prehistory = True
releases_document_name = "history"
releases_issue_uri = "https://github.com/tmux-python/tmuxp/issues/%s"
releases_release_uri = "https://github.com/tmux-python/tmuxp/tree/v%s"

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = about['__title__']
copyright = about['__copyright__']

version = '%s' % ('.'.join(about['__version__'].split('.'))[:2])
release = '%s' % (about['__version__'])

exclude_patterns = ['_build']

pygments_style = 'sphinx'

html_theme_path = [alagitpull.get_path()]
html_favicon = 'favicon.ico'
html_theme = 'alagitpull'
html_static_path = ['_static']
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'more.html',
        'book.html',
        'searchbox.html',
    ]
}

html_theme_options = {
    'logo': 'img/tmuxp.svg',
    'github_user': 'tmux-python',
    'github_repo': 'tmuxp',
    'github_type': 'star',
    'github_banner': True,
    'projects': alagitpull.projects,
    'project_name': about['__title__'],
}

alagitpull_internal_hosts = [
    'tmuxp.git-pull.com',
    '0.0.0.0',
]
alagitpull_external_hosts_new_window = True

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
    'python': ('https://docs.python.org/', None),
    'libtmux': ('https://libtmux.readthedocs.io/en/latest', None)
}

# aafig format, try to get working with pdf
aafig_format = dict(latex='pdf', html='gif')

aafig_default_options = dict(
    scale=.75,
    aspect=0.5,
    proportional=True,
)
