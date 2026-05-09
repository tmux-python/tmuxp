"""tmuxinator fixture: `socket_path` passes through to tmuxp top-level."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file(
    "import_tmuxinator/test_socket_path.yaml",
)
tmuxinator_dict = {
    "name": "sock-project",
    "socket_path": "/tmp/my-tmux.sock",
    "windows": [{"editor": "vim"}],
}
expected = {
    "session_name": "sock-project",
    "socket_path": "/tmp/my-tmux.sock",
    "windows": [{"window_name": "editor", "panes": ["vim"]}],
}
