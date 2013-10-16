"""
tmuxp
-----

A Pythonic ORM Toolkit for managing tmux(1) workspaces.


"""
from setuptools import setup
try:
    from pip.req import parse_requirements
except ImportError:
    def requirements(f):
        reqs = open(f, 'r').read().splitlines()
        reqs = [r for r in reqs if not r.strip().startswith('#')]
        return reqs
else:
    def requirements(f):
        install_reqs = parse_requirements(f)
        reqs = [str(r.req) for r in install_reqs]
        return reqs

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
    description='Manage and build tmux workspaces.',
    long_description=open('README.rst').read(),
    packages=['tmuxp', 'tmuxp.testsuite'],
    include_package_data=True,
    install_requires=requirements('requirements.pip'),
    scripts=['pkg/tmuxp.bash', 'pkg/tmuxp.zsh'],
    entry_points=dict(console_scripts=['tmuxp=tmuxp:main']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        "Topic :: Utilities",
        "Topic :: System :: Shells",
    ],
)
