"""A minimal valid custom workspace builder used by resolution tests."""

from __future__ import annotations

from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder


class CustomBuilder(ClassicWorkspaceBuilder):
    """Trivial subclass that satisfies the workspace builder contract."""
