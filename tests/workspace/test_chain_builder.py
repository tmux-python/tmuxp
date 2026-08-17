"""Tests for the chain-based workspace builder."""

from __future__ import annotations

import typing as t

from libtmux.test.retry import retry_until
from libtmux.window import Window

from tests.fixtures import utils as test_utils
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.workspace import loader
from tmuxp.workspace.chain_builder import ChainWorkspaceBuilder

if t.TYPE_CHECKING:
    from libtmux.session import Session


def _load(name: str) -> dict[str, t.Any]:
    workspace = ConfigReader._from_file(
        test_utils.get_workspace_file(f"workspace/builder/{name}"),
    )
    workspace = loader.expand(workspace)
    return loader.trickle(workspace)


def test_chain_split_windows(session: Session) -> None:
    """The chain builder creates the windows and panes of a two-pane workspace."""
    workspace = _load("two_pane.yaml")
    builder = ChainWorkspaceBuilder(session_config=workspace, server=session.server)

    builder.build(session=session)

    assert builder.session is session
    assert [w.name for w in session.windows] == ["editor", "logging", "test"]

    editor = session.windows.get(window_name="editor")
    assert isinstance(editor, Window)
    editor.refresh()
    assert len(editor.panes) == 2


def test_chain_three_pane(session: Session) -> None:
    """The chain builder splits a window into three panes."""
    workspace = _load("three_pane.yaml")
    builder = ChainWorkspaceBuilder(session_config=workspace, server=session.server)

    builder.build(session=session)

    test_window = session.windows.get(window_name="test")
    assert isinstance(test_window, Window)
    test_window.refresh()
    assert len(test_window.panes) == 3


def test_chain_focus(session: Session) -> None:
    """The chain builder honours window and pane focus."""
    workspace = _load("focus_and_pane.yaml")
    builder = ChainWorkspaceBuilder(session_config=workspace, server=session.server)

    builder.build(session=session)

    assert session.active_window.name == "focused window"


def test_chain_commands_landed(session: Session) -> None:
    """Readiness mode delivers each pane's shell command."""
    workspace = loader.trickle(
        loader.expand(
            {
                "session_name": "cc_cmd",
                "windows": [
                    {
                        "window_name": "marker",
                        "panes": [{"shell_command": "echo CC_LANDED"}],
                    },
                ],
            },
        ),
    )
    builder = ChainWorkspaceBuilder(session_config=workspace, server=session.server)
    builder.build(session=session)

    window = session.windows.get(window_name="marker")
    assert isinstance(window, Window)
    pane = window.active_pane
    assert pane is not None

    def _landed() -> bool:
        return any("CC_LANDED" in line for line in pane.capture_pane())

    assert retry_until(_landed, 2)


def test_chain_batched_mode(session: Session) -> None:
    """Batched mode folds send_keys into the plan and still builds the tree."""
    workspace = _load("two_pane.yaml")
    builder = ChainWorkspaceBuilder(
        session_config=workspace,
        server=session.server,
        send_keys_mode="batched",
    )

    builder.build(session=session)

    assert [w.name for w in session.windows] == ["editor", "logging", "test"]
    editor = session.windows.get(window_name="editor")
    assert isinstance(editor, Window)
    editor.refresh()
    assert len(editor.panes) == 2


def test_cli_builder_flag() -> None:
    """The load CLI exposes --builder with default and chain choices."""
    import argparse

    from tmuxp.cli.load import create_load_subparser

    parser = create_load_subparser(argparse.ArgumentParser())
    assert parser.parse_args(["ws.yaml", "--builder", "chain"]).builder == "chain"
    assert parser.parse_args(["ws.yaml"]).builder == "default"
