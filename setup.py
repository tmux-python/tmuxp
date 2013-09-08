"""
tmuxp
-----

a python ORM for tmux(1).


"""
from setuptools import setup

setup(
    name='tmuxp',
    version='0.1-dev',
    url='http://github.com/tony/tmuxp/',
    license='BSD',
    author='Tony Narlock',
    author_email='tony@git-pull.com',
    description='An object mapper and workspace manager for tmux',
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
