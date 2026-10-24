"""teamocil v1.x fixture: bare string pane -> shell_command list."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

teamocil_yaml = test_utils.read_workspace_file(
    "import_teamocil/test_v1x_string_pane.yaml",
)
teamocil_dict = {
    "name": "v1x-string",
    "windows": [{"name": "editor", "panes": ["vim", "top"]}],
}
expected = {
    "session_name": "v1x-string",
    "windows": [
        {
            "window_name": "editor",
            "panes": [
                {"shell_command": ["vim"]},
                {"shell_command": ["top"]},
            ],
        },
    ],
}
