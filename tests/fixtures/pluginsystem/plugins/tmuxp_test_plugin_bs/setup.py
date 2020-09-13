from setuptools import setup

setup(
    name='tmuxp_test_plugin_bs',
    version='0.0.2',
    author='Joseph Flinn',
    author_email='joseph.s.flinn@gmail.com',
    packages=setuptools.find_packages(),
    description=(
        'A tmuxp plugin to test the before_script part of the plugin system'
    ),
)
