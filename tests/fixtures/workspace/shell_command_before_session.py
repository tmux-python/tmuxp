"""Tests shell_command_before configuration."""

from __future__ import annotations

from tests.fixtures import utils as test_utils

before = test_utils.read_workspace_file("workspace/shell_command_before_session.yaml")
expected = test_utils.read_workspace_file(
    "workspace/shell_command_before_session-expected.yaml",
)
