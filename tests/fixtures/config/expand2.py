import os

from .. import utils as test_utils

unexpanded_yaml = test_utils.read_config_file("config/expand2-unexpanded.yaml")
expanded_yaml = test_utils.read_config_file("config/expand2-expanded.yaml").format(
    HOME=os.path.expanduser("~")
)
