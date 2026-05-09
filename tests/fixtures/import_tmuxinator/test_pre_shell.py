"""tmuxinator fixture: `pre` with shell metacharacters triggers warning."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file(
    "import_tmuxinator/test_pre_shell.yaml",
)
tmuxinator_dict = {
    "name": "shell-pre",
    "pre": "echo a | grep b && echo done",
    "windows": [{"editor": "vim"}],
}
expected = {
    "session_name": "shell-pre",
    "before_script": "echo a | grep b && echo done",
    "windows": [{"window_name": "editor", "panes": ["vim"]}],
}
