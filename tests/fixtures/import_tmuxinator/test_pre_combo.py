"""tmuxinator fixture: `pre` + `pre_window` map independently."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file(
    "import_tmuxinator/test_pre_combo.yaml",
)
tmuxinator_dict = {
    "name": "combo",
    "pre": "sudo /etc/rc.d/mysqld start",
    "pre_window": ["echo first", "echo second"],
    "windows": [{"editor": "vim"}],
}
expected = {
    "session_name": "combo",
    "before_script": "sudo /etc/rc.d/mysqld start",
    "shell_command_before": ["echo first", "echo second"],
    "windows": [{"window_name": "editor", "panes": ["vim"]}],
}
