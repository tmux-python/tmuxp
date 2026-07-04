"""Tmuxinator data fixtures for import_tmuxinator tests, 6th dataset."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

tmuxinator_yaml = test_utils.read_workspace_file("import_tmuxinator/test6.yaml")

tmuxinator_dict = {
    "name": "sync-test",
    "root": "~/projects/sync",
    "windows": [
        {
            "synced": {
                "synchronize": True,
                "panes": ["echo 'pane1'", "echo 'pane2'"],
            },
        },
        {
            "synced-after": {
                "synchronize": "after",
                "panes": ["echo 'pane1'"],
            },
        },
        {
            "not-synced": {
                "synchronize": False,
                "panes": ["echo 'pane1'"],
            },
        },
    ],
}

expected = {
    "session_name": "sync-test",
    "start_directory": "~/projects/sync",
    "windows": [
        {
            "window_name": "synced",
            "options": {"synchronize-panes": "on"},
            "panes": ["echo 'pane1'", "echo 'pane2'"],
        },
        {
            "window_name": "synced-after",
            "options_after": {"synchronize-panes": "on"},
            "panes": ["echo 'pane1'"],
        },
        {
            "window_name": "not-synced",
            "panes": ["echo 'pane1'"],
        },
    ],
}
