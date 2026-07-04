"""tmuxinator fixture: `rvm` -> shell_command_before with `rvm use` wrapper."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file("import_tmuxinator/test_rvm.yaml")
tmuxinator_dict = {
    "name": "rvm-project",
    "rvm": "3.2.0",
    "windows": [{"editor": "vim"}],
}
expected = {
    "session_name": "rvm-project",
    "shell_command_before": ["rvm use 3.2.0"],
    "windows": [{"window_name": "editor", "panes": ["vim"]}],
}
