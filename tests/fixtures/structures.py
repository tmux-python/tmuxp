"""Typings / structures for tmuxp fixtures."""
import dataclasses
import typing as t


@dataclasses.dataclass
class WorkspaceTestData:
    """Workspace data fixtures for tmuxp tests."""

    expand1: t.Any
    expand2: t.Any
    expand_blank: t.Any
    sample_workspace: t.Any
    shell_command_before: t.Any
    shell_command_before_session: t.Any
    trickle: t.Any
