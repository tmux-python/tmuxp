"""Tests for the engine-ops (async, folding) workspace builder."""

from __future__ import annotations

import contextlib
import typing as t

import pytest

from tmuxp import exc
from tmuxp.workspace.builder.engine_ops import EngineOpsWorkspaceBuilder
from tmuxp.workspace.builder.protocol import WorkspaceBuilderProtocol
from tmuxp.workspace.builder.registry import resolve_builder_class

if t.TYPE_CHECKING:
    import pathlib

    from libtmux.server import Server
    from libtmux.session import Session


def _kill(server: Server, session_name: str) -> None:
    """Kill *session_name* if present, so a build leaves the server clean."""
    with contextlib.suppress(Exception):
        sess = server.sessions.get(session_name=session_name)
        if sess is not None:
            sess.kill()


class _BuildCase(t.NamedTuple):
    """A workspace config and the window/pane shape it should build."""

    test_id: str
    config: dict[str, t.Any]
    windows: int
    panes_per_window: list[int]


_BUILD_CASES: tuple[_BuildCase, ...] = (
    _BuildCase(
        test_id="single_window_two_panes",
        config={
            "session_name": "eo-two",
            "windows": [{"window_name": "editor", "panes": ["echo a", "echo b"]}],
        },
        windows=1,
        panes_per_window=[2],
    ),
    _BuildCase(
        test_id="two_windows_mixed_panes",
        config={
            "session_name": "eo-mixed",
            "windows": [
                {"window_name": "editor", "panes": ["echo a", "echo b", "echo c"]},
                {"window_name": "logs", "panes": ["echo tail"]},
            ],
        },
        windows=2,
        panes_per_window=[3, 1],
    ),
)


@pytest.mark.parametrize("case", _BUILD_CASES, ids=[c.test_id for c in _BUILD_CASES])
def test_engine_ops_build_shape(case: _BuildCase, session: Session) -> None:
    """The folding async build creates the declared windows and panes."""
    server = session.server
    builder = EngineOpsWorkspaceBuilder(session_config=case.config, server=server)
    try:
        builder.build()
        built = builder.session
        assert built.name == case.config["session_name"]
        assert len(built.windows) == case.windows
        assert [len(w.panes) for w in built.windows] == case.panes_per_window
    finally:
        _kill(server, case.config["session_name"])


class _EngineCase(t.NamedTuple):
    """An engine_ops_engine choice for the builder."""

    test_id: str
    engine_ops_engine: str


_ENGINE_CASES: tuple[_EngineCase, ...] = (
    _EngineCase(test_id="subprocess", engine_ops_engine="subprocess"),
    _EngineCase(test_id="control_mode", engine_ops_engine="control_mode"),
)


@pytest.mark.parametrize("case", _ENGINE_CASES, ids=[c.test_id for c in _ENGINE_CASES])
def test_engine_ops_engine_choice_builds(case: _EngineCase, session: Session) -> None:
    """The engine_ops_engine key selects the async engine and still builds."""
    server = session.server
    session_name = f"eo-eng-{case.test_id}"
    config = {
        "session_name": session_name,
        "engine_ops_engine": case.engine_ops_engine,
        "windows": [
            {"window_name": "w0", "panes": ["echo a", "echo b"]},
            {"window_name": "w1", "panes": ["echo c"]},
        ],
    }
    builder = EngineOpsWorkspaceBuilder(session_config=config, server=server)
    try:
        builder.build()
        built = builder.session
        assert built.name == session_name
        assert [len(w.panes) for w in built.windows] == [2, 1]
    finally:
        _kill(server, session_name)


def test_engine_ops_satisfies_protocol(session: Session) -> None:
    """The builder is a conforming WorkspaceBuilderProtocol instance."""
    builder = EngineOpsWorkspaceBuilder(
        session_config={"session_name": "eo-proto", "windows": [{"panes": ["echo x"]}]},
        server=session.server,
    )
    assert isinstance(builder, WorkspaceBuilderProtocol)


def test_engine_ops_resolves_via_entry_point() -> None:
    """The ``workspace_builder: engine-ops`` config selects this builder."""
    resolved = resolve_builder_class({"workspace_builder": "engine-ops"})
    assert resolved is EngineOpsWorkspaceBuilder


def test_engine_ops_emits_build_events(session: Session) -> None:
    """Structural events are forwarded, ending with workspace_built."""
    events: list[dict[str, t.Any]] = []
    builder = EngineOpsWorkspaceBuilder(
        session_config={
            "session_name": "eo-events",
            "windows": [{"window_name": "w", "panes": ["echo a", "echo b"]}],
        },
        server=session.server,
        on_build_event=events.append,
    )
    try:
        builder.build()
        names = [e["event"] for e in events]
        assert names[0] == "session_created"
        assert names[-1] == "workspace_built"
        assert "pane_created" in names
    finally:
        _kill(session.server, "eo-events")


def test_engine_ops_append_unsupported(session: Session) -> None:
    """Append is not expressible in the IR; the builder refuses it."""
    builder = EngineOpsWorkspaceBuilder(
        session_config={
            "session_name": "eo-append",
            "windows": [{"panes": ["echo x"]}],
        },
        server=session.server,
    )
    with pytest.raises(NotImplementedError, match="append"):
        builder.build(append=True)


def test_engine_ops_empty_config_raises(session: Session) -> None:
    """An empty config fails fast, matching the classic builder."""
    with pytest.raises(exc.EmptyWorkspaceException):
        EngineOpsWorkspaceBuilder(session_config={}, server=session.server)


def test_engine_ops_cli_flag_builds(server: Server, tmp_path: pathlib.Path) -> None:
    """`tmuxp load --engine-ops` routes a config through the engine-ops builder."""
    from tmuxp import cli

    socket_name = server.socket_name
    assert socket_name is not None
    config = tmp_path / "ws.yaml"
    config.write_text(
        "session_name: eo-cli\nwindows:\n  - panes: [echo a, echo b]\n",
    )
    try:
        with contextlib.suppress(SystemExit):
            cli.cli(
                [
                    "load",
                    str(config),
                    "--engine-ops",
                    "-d",
                    "-L",
                    socket_name,
                    "-y",
                ],
            )
        assert server.has_session("eo-cli")
        built = server.sessions.get(session_name="eo-cli")
        assert built is not None
        assert len(built.windows[0].panes) == 2
    finally:
        _kill(server, "eo-cli")
