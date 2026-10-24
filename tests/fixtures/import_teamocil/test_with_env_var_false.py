"""teamocil fixture: explicit with_env_var=false suppresses the env var."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

teamocil_yaml = test_utils.read_workspace_file(
    "import_teamocil/test_with_env_var_false.yaml",
)
teamocil_dict = {
    "session": {
        "name": "env-off",
        "with_env_var": False,
        "windows": [{"name": "main", "panes": [{"cmd": "echo hi"}]}],
    },
}
expected = {
    "session_name": "env-off",
    "windows": [
        {"window_name": "main", "panes": [{"shell_command": "echo hi"}]},
    ],
}
