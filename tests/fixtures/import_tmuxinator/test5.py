"""Tmuxinator data fixtures for import_tmuxinator tests, 5th dataset."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file("import_tmuxinator/test5.yaml")

tmuxinator_dict = {
    "name": "ruby-app",
    "root": "~/projects/ruby-app",
    "rvm": "2.1.1",
    "pre": "./scripts/bootstrap.sh",
    "pre_tab": "source .env",
    "startup_window": "server",
    "startup_pane": 0,
    "windows": [
        {"editor": "vim"},
        {"server": "rails s"},
    ],
}

expected = {
    "session_name": "ruby-app",
    "start_directory": "~/projects/ruby-app",
    "on_project_start": "./scripts/bootstrap.sh",
    "shell_command_before": ["rvm use 2.1.1"],
    "windows": [
        {"window_name": "editor", "panes": ["vim"]},
        {
            "window_name": "server",
            "focus": True,
            "panes": [{"shell_command": ["rails s"], "focus": True}],
        },
    ],
}
