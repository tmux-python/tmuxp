"""Teamocil data fixtures for import_teamocil tests, 6th test."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

teamocil_yaml = test_utils.read_workspace_file("import_teamocil/test6.yaml")

teamocil_dict = {
    "windows": [
        {
            "name": "focused-window",
            "root": "~/Code/app",
            "layout": "main-vertical",
            "focus": True,
            "options": {"synchronize-panes": "on"},
            "panes": [
                {"cmd": "vim"},
                {"cmd": "rails s", "height": 30},
            ],
        },
        {
            "name": "background-window",
            "panes": [{"cmd": "tail -f log/development.log"}],
        },
    ],
}

expected = {
    "session_name": None,
    "windows": [
        {
            "window_name": "focused-window",
            "start_directory": "~/Code/app",
            "layout": "main-vertical",
            "focus": True,
            "options": {"synchronize-panes": "on"},
            "panes": [
                {"shell_command": "vim"},
                {"shell_command": "rails s"},
            ],
        },
        {
            "window_name": "background-window",
            "panes": [{"shell_command": "tail -f log/development.log"}],
        },
    ],
}
