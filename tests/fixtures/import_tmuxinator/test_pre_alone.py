"""tmuxinator fixture: solo `pre` maps to `before_script`."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file(
    "import_tmuxinator/test_pre_alone.yaml",
)
tmuxinator_dict = {
    "name": "alone",
    "root": "~/test",
    "pre": "sudo /etc/rc.d/mysqld start",
    "windows": [{"editor": "vim"}],
}
expected = {
    "session_name": "alone",
    "start_directory": "~/test",
    "before_script": "sudo /etc/rc.d/mysqld start",
    "windows": [{"window_name": "editor", "panes": ["vim"]}],
}
