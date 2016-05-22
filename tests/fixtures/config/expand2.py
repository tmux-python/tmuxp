import os

from .._util import loadfixture

unexpanded_yaml = loadfixture('config/expand2-unexpanded.yaml')
expanded_yaml = loadfixture('config/expand2-expanded.yaml').format(
    HOME=os.path.expanduser('~')
)
