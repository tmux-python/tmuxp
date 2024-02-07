"""YAML examples of expansion of tmuxp configurations from shorthand style."""
import pathlib

from .. import utils as test_utils


def unexpanded_yaml() -> str:
    """Return unexpanded, shorthand YAML tmuxp configuration."""
    return test_utils.read_workspace_file("workspace/expand2-unexpanded.yaml")


def expanded_yaml() -> str:
    """Return expanded, verbose YAML tmuxp configuration."""
    return test_utils.read_workspace_file("workspace/expand2-expanded.yaml").format(
        HOME=str(pathlib.Path().home()),
    )
