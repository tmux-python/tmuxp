"""Workspace builders: turn an expanded workspace ``dict`` into a tmux session.

:class:`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder` is the default
implementation. A workspace may select a different builder with the
``workspace_builder`` config key, resolved by
:mod:`tmuxp.workspace.builder.registry`.

``WorkspaceBuilder`` remains importable here as a backwards-compatible alias of
:class:`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder`.

The experimental
:class:`~tmuxp.workspace.builder.chain.ChainWorkspaceBuilder` is also exported.
Its module imports cleanly even when libtmux's unreleased chain API
(libtmux#685) is absent; the missing API surfaces only when its ``build()`` runs.
"""

from __future__ import annotations

from tmuxp.workspace.builder.chain import ChainWorkspaceBuilder
from tmuxp.workspace.builder.classic import (
    ClassicWorkspaceBuilder,
    get_default_columns,
    get_default_rows,
)
from tmuxp.workspace.builder.protocol import WorkspaceBuilderProtocol
from tmuxp.workspace.builder.registry import (
    WORKSPACE_BUILDERS_GROUP,
    available_builders,
    prepended_sys_path,
    resolve_builder_class,
    resolve_builder_paths,
)

# Backwards-compatible alias: the classic builder was historically named
# ``WorkspaceBuilder`` and imported from ``tmuxp.workspace.builder``.
WorkspaceBuilder = ClassicWorkspaceBuilder

__all__ = [
    "WORKSPACE_BUILDERS_GROUP",
    "ChainWorkspaceBuilder",
    "ClassicWorkspaceBuilder",
    "WorkspaceBuilder",
    "WorkspaceBuilderProtocol",
    "available_builders",
    "get_default_columns",
    "get_default_rows",
    "prepended_sys_path",
    "resolve_builder_class",
    "resolve_builder_paths",
]
