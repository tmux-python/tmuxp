"""tmuxinator fixture: cli_args with -f, -L, -S all extracted."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file(
    "import_tmuxinator/test_cli_args_multi.yaml",
)
tmuxinator_dict = {
    "name": "multi-flags",
    "cli_args": "-f ~/.tmux.conf -L mysock -S /tmp/tmux.sock",
    "windows": [{"editor": "vim"}],
}
expected = {
    "session_name": "multi-flags",
    "config": "~/.tmux.conf",
    "socket_name": "mysock",
    "socket_path": "/tmp/tmux.sock",
    "windows": [{"window_name": "editor", "panes": ["vim"]}],
}
