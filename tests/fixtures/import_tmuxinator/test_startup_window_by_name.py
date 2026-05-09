"""tmuxinator fixture: `startup_window` resolved by window name."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file(
    "import_tmuxinator/test_startup_window_by_name.yaml",
)
tmuxinator_dict = {
    "name": "focus-by-name",
    "startup_window": "editor",
    "windows": [{"shell": "bash"}, {"editor": "vim"}, {"logs": "tail -f log"}],
}
expected = {
    "session_name": "focus-by-name",
    "windows": [
        {"window_name": "shell", "panes": ["bash"]},
        {"window_name": "editor", "panes": ["vim"], "focus": True},
        {"window_name": "logs", "panes": ["tail -f log"]},
    ],
}
