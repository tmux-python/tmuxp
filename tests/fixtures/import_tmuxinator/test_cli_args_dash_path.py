"""tmuxinator fixture: tmux_options path containing literal `-f` (regression)."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file(
    "import_tmuxinator/test_cli_args_dash_path.yaml",
)
tmuxinator_dict = {
    "name": "dash-path",
    "tmux_options": "-f /home/me/-f-config.conf",
    "windows": [{"editor": "vim"}],
}
expected = {
    "session_name": "dash-path",
    "config": "/home/me/-f-config.conf",
    "windows": [{"window_name": "editor", "panes": ["vim"]}],
}
