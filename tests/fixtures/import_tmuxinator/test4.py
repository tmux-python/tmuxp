"""Tmuxinator data fixtures for import_tmuxinator tests, 4th dataset."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file("import_tmuxinator/test4.yaml")

tmuxinator_dict = {
    "name": "multi-flag",
    "root": "~/projects/app",
    "cli_args": "-f ~/.tmux.mac.conf -L mysocket",
    "windows": [
        {"editor": "vim"},
        {"server": "rails s"},
    ],
}

expected = {
    "session_name": "multi-flag",
    "start_directory": "~/projects/app",
    "config": "~/.tmux.mac.conf",
    "socket_name": "mysocket",
    "windows": [
        {"window_name": "editor", "panes": ["vim"]},
        {"window_name": "server", "panes": ["rails s"]},
    ],
}
