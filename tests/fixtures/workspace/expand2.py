import os

from .. import utils as test_utils


def unexpanded_yaml():
    return test_utils.read_workspace_file("workspace/expand2-unexpanded.yaml")


def expanded_yaml():
    return test_utils.read_workspace_file("workspace/expand2-expanded.yaml").format(
        HOME=os.path.expanduser("~")
    )
