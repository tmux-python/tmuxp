import pathlib

from .. import utils as test_utils


def unexpanded_yaml() -> str:
    return test_utils.read_workspace_file("workspace/expand2-unexpanded.yaml")


def expanded_yaml() -> str:
    return test_utils.read_workspace_file("workspace/expand2-expanded.yaml").format(
        HOME=str(pathlib.Path().home())
    )
