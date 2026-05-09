"""teamocil v1.x fixture: commands, focus, options, mixed pane forms."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

teamocil_yaml = test_utils.read_workspace_file("import_teamocil/test_v1x_full.yaml")
teamocil_dict = {
    "name": "v1x-full",
    "root": "~/proj",
    "windows": [
        {
            "name": "editor",
            "root": "~/proj/src",
            "layout": "main-vertical",
            "focus": True,
            "options": {"main-pane-width": "120"},
            "panes": [
                {"commands": ["vim"], "focus": True},
                "top",
            ],
        },
        {"name": "shell", "panes": ["bash"]},
    ],
}
expected = {
    "session_name": "v1x-full",
    "start_directory": "~/proj",
    "windows": [
        {
            "window_name": "editor",
            "start_directory": "~/proj/src",
            "layout": "main-vertical",
            "focus": True,
            "options": {"main-pane-width": "120"},
            "panes": [
                {"shell_command": ["vim"], "focus": True},
                {"shell_command": ["top"]},
            ],
        },
        {
            "window_name": "shell",
            "panes": [{"shell_command": ["bash"]}],
        },
    ],
}
