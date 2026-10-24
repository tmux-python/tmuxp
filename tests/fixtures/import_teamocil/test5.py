"""Teamocil data fixtures for import_teamocil tests, 5th test (v1.x format)."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

teamocil_yaml = test_utils.read_workspace_file("import_teamocil/test5.yaml")

teamocil_dict = {
    "windows": [
        {
            "name": "v1-string-panes",
            "root": "~/Code/legacy",
            "layout": "even-horizontal",
            "panes": ["echo 'hello'", "echo 'world'", None],
        },
        {
            "name": "v1-commands-key",
            "panes": [{"commands": ["pwd", "ls -la"]}],
        },
    ],
}

expected = {
    "session_name": None,
    "windows": [
        {
            "window_name": "v1-string-panes",
            "start_directory": "~/Code/legacy",
            "layout": "even-horizontal",
            "panes": [
                {"shell_command": ["echo 'hello'"]},
                {"shell_command": ["echo 'world'"]},
                {"shell_command": []},
            ],
        },
        {
            "window_name": "v1-commands-key",
            "panes": [{"shell_command": ["pwd", "ls -la"]}],
        },
    ],
}
