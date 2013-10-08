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


setup(
    name='tmuxp',
    version='0.0.1-dev',
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
    entry_points=dict(console_scripts=['tmuxp=tmuxp:main']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        "License :: OSI Approved :: BSD License",
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        "Topic :: Utilities",
        "Topic :: System :: Shells",
    ],
)
