import os

from .._util import read_config_file

unexpanded_yaml = read_config_file("config/expand2-unexpanded.yaml")
expanded_yaml = read_config_file("config/expand2-expanded.yaml").format(
    HOME=os.path.expanduser("~")
)
