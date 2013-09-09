"""
tmuxp
-----

A Pythonic ORM Toolkit for managing tmux(1) workspaces.


"""
from setuptools import setup

setup(
    name='tmuxp',
    version='0.1-dev',
    url='http://github.com/tony/tmuxp/',
    license='BSD',
    author='Tony Narlock',
    author_email='tony@git-pull.com',
    description='Manage and build tmux workspaces.',
    packages=['tmuxp', 'tmuxp.testsuite'],
    include_package_data=True,
    install_requires=[
        'logutils',
        'kaptan',
        'sh'
    ],
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
