"""tmuxinator fixture: `startup_window` resolved by 0-based index."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file(
    "import_tmuxinator/test_startup_window_by_index.yaml",
)
tmuxinator_dict = {
    "name": "focus-by-idx",
    "startup_window": 2,
    "windows": [{"shell": "bash"}, {"editor": "vim"}, {"logs": "tail -f log"}],
}
expected = {
    "session_name": "focus-by-idx",
    "windows": [
        {"window_name": "shell", "panes": ["bash"]},
        {"window_name": "editor", "panes": ["vim"]},
        {"window_name": "logs", "panes": ["tail -f log"], "focus": True},
    ],
}
