"""tmuxp lives at <https://github.com/tony/tmuxp>.

tmuxp
-----

Manage tmux workspaces from JSON and YAML, pythonic API, shell completion.

"""
import os
import sys

from setuptools import setup

about = {}
with open("tmuxp/__about__.py") as fp:
    exec(fp.read(), about)

with open('requirements.pip') as f:
    install_reqs = [line for line in f.read().split('\n') if line]
    tests_reqs = []

if sys.version_info < (2, 7):
    install_reqs += ['argparse']
    tests_reqs += ['unittest2']

readme = open('README.rst').read()
history = open('CHANGES').read().replace('.. :changelog:', '')

setup(
    name=about['__title__'],
    version=about['__version__'],
    url='http://github.com/tony/tmuxp/',
    download_url='https://pypi.python.org/pypi/tmuxp',
    license=about['__license__'],
    author=about['__author__'],
    author_email=about['__email__'],
    description=about['__description__'],
    long_description=readme,
    packages=['tmuxp', 'tmuxp.testsuite',
              'tmuxp._vendor', 'tmuxp._vendor.colorama'],
    include_package_data=True,
    install_requires=install_reqs,
    tests_require=tests_reqs,
    test_suite='tmuxp.testsuite',
    zip_safe=False,
    keywords=about['__title__'],
    scripts=['pkg/tmuxp.bash', 'pkg/tmuxp.zsh', 'pkg/tmuxp.tcsh'],
    entry_points=dict(console_scripts=['tmuxp=tmuxp:cli.main']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        "Topic :: Utilities",
        "Topic :: System :: Shells",
    ],
)
