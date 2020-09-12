from setuptools import setup

setup(
    name='tmuxp_test_plugin_bwb',
    version='0.0.1',
    author='Joseph Flinn',
    author_email='joseph.s.flinn@gmail.com',
    packages=setuptools.find_packages(),
    description=(
        'A tmuxp plugin to test the before_workspace_builder part of the '
        'plugin system'
    ),
)
