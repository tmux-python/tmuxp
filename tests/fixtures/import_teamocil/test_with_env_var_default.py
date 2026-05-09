"""teamocil fixture: v0.x default with_env_var=true exports TEAMOCIL=1."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

teamocil_yaml = test_utils.read_workspace_file(
    "import_teamocil/test_with_env_var_default.yaml",
)
teamocil_dict = {
    "session": {
        "name": "env-default",
        "windows": [{"name": "main", "panes": [{"cmd": "echo hi"}]}],
    },
}
expected = {
    "session_name": "env-default",
    "environment": {"TEAMOCIL": "1"},
    "windows": [
        {"window_name": "main", "panes": [{"shell_command": "echo hi"}]},
    ],
}
