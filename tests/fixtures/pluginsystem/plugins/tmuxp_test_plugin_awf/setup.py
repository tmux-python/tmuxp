from setuptools import setup

setup(
    name='tmuxp_test_plugin_awf',
    version='0.0.1',
    author='Joseph Flinn',
    author_email='joseph.s.flinn@gmail.com',
    packages=setuptools.find_packages(),
    description=(
        'A tmuxp plugin to test the after_window_finished part of the '
        'plugin system'
    ),
)
