"""Tests for ChainWorkspaceBuilder when the libtmux chain API is absent.

Unlike :mod:`tests.workspace.test_builder_chain`, this module does not require
the unreleased chain API (libtmux#685): it asserts the import-guarded fallback.
On released libtmux the chain API is absent, so selecting ``workspace_builder:
chain`` must resolve cleanly and only fail with
:exc:`~tmuxp.exc.WorkspaceBuilderImportError` when ``build()`` runs. The module
self-skips on the rare build where the chain API is present.
"""

from __future__ import annotations

import typing as t

import pytest

from tmuxp import exc
from tmuxp.workspace import loader
from tmuxp.workspace.builder import registry
from tmuxp.workspace.builder.chain import _HAVE_CHAIN, ChainWorkspaceBuilder

if t.TYPE_CHECKING:
    from libtmux.server import Server

pytestmark = pytest.mark.skipif(
    _HAVE_CHAIN,
    reason="libtmux chain API present; the unavailable path cannot be exercised",
)


class SelectionCase(t.NamedTuple):
    """A way of selecting the chain builder from a workspace config."""

    test_id: str
    workspace_builder: str


SELECTION_CASES: list[SelectionCase] = [
    SelectionCase(test_id="entry_point_name", workspace_builder="chain"),
    SelectionCase(
        test_id="dotted_reference",
        workspace_builder="tmuxp.workspace.builder.chain:ChainWorkspaceBuilder",
    ),
]


@pytest.mark.parametrize(
    "case",
    SELECTION_CASES,
    ids=[c.test_id for c in SELECTION_CASES],
)
def test_chain_selection_resolves(case: SelectionCase) -> None:
    """Selecting the chain builder resolves to the class without the chain API."""
    config = loader.expand(
        {
            "session_name": "chain-unavailable",
            "workspace_builder": case.workspace_builder,
            "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
        },
    )

    resolved = registry.resolve_builder_class(config)

    assert resolved is ChainWorkspaceBuilder


@pytest.mark.parametrize(
    "case",
    SELECTION_CASES,
    ids=[c.test_id for c in SELECTION_CASES],
)
def test_chain_build_raises_import_error(case: SelectionCase, server: Server) -> None:
    """Building with the chain API absent raises WorkspaceBuilderImportError."""
    config = loader.expand(
        {
            "session_name": "chain-unavailable",
            "workspace_builder": case.workspace_builder,
            "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
        },
    )
    builder_cls = registry.resolve_builder_class(config)
    builder = builder_cls(session_config=config, server=server)

    with pytest.raises(exc.WorkspaceBuilderImportError):
        builder.build()
