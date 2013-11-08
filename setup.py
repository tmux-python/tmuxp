"""tmuxp lives at <https://github.com/tony/tmuxp>.

tmuxp
-----

Manage tmux workspaces from JSON and YAML, pythonic API, shell completion.

"""
import sys
from setuptools import setup

with open('requirements.pip') as f:
    install_reqs = [line for line in f.read().split('\n') if line]
    tests_reqs = []

if sys.version_info < (2, 7):
    install_reqs += ['argparse']
    tests_reqs += ['unittest2']

import re
VERSIONFILE = "tmuxp/__init__.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    __version__ = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))


setup(
    name='tmuxp',
    version=__version__,
    url='http://github.com/tony/tmuxp/',
    download_url='https://pypi.python.org/pypi/tmuxp',
    license='BSD',
    author='Tony Narlock',
    author_email='tony@git-pull.com',
    description='Manage tmux workspaces from JSON and YAML, pythonic API, '
                'shell completion',
    long_description=open('README.rst').read(),
    packages=['tmuxp', 'tmuxp.testsuite',
              'tmuxp._vendor', 'tmuxp._vendor.colorama'],
    include_package_data=True,
    install_requires=install_reqs,
    tests_require=tests_reqs,
    test_suite='tmuxp.testsuite',
    zip_safe=False,
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
