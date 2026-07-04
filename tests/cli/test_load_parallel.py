"""Tests for ``tmuxp load --parallel`` (engine-ops workspace set)."""

from __future__ import annotations

import contextlib
import typing as t

import pytest

from tmuxp import cli

if t.TYPE_CHECKING:
    import pathlib

    from libtmux.server import Server


def _kill(server: Server, *session_names: str) -> None:
    """Kill each named session if present, leaving the server clean."""
    for name in session_names:
        with contextlib.suppress(Exception):
            sess = server.sessions.get(session_name=name, default=None)
            if sess is not None:
                sess.kill()


def _write_workspace(
    path: pathlib.Path,
    session_name: str,
    panes: list[str],
) -> None:
    """Write a minimal single-window workspace file with *panes*."""
    pane_list = ", ".join(panes)
    path.write_text(
        f"session_name: {session_name}\nwindows:\n  - panes: [{pane_list}]\n",
        encoding="utf-8",
    )


class _ParallelCase(t.NamedTuple):
    """A batch of workspaces and the pane count each should build."""

    test_id: str
    # (session_name, pane commands) per workspace file, in declaration order.
    sessions: tuple[tuple[str, list[str]], ...]


_PARALLEL_CASES: tuple[_ParallelCase, ...] = (
    _ParallelCase(
        test_id="single_file_set",
        sessions=(("ppar-solo", ["echo a", "echo b"]),),
    ),
    _ParallelCase(
        test_id="two_file_set",
        sessions=(
            ("ppar-a", ["echo a1", "echo a2"]),
            ("ppar-b", ["echo b1"]),
        ),
    ),
)


@pytest.mark.parametrize(
    "case",
    _PARALLEL_CASES,
    ids=[c.test_id for c in _PARALLEL_CASES],
)
def test_parallel_builds_all_sessions(
    case: _ParallelCase,
    server: Server,
    tmp_path: pathlib.Path,
) -> None:
    """``--parallel`` builds every file's session as one folded set."""
    assert server.socket_name is not None
    files: list[str] = []
    names: list[str] = []
    for idx, (session_name, panes) in enumerate(case.sessions):
        cfg = tmp_path / f"ws{idx}.yaml"
        _write_workspace(cfg, session_name, panes)
        files.append(str(cfg))
        names.append(session_name)
    try:
        with contextlib.suppress(SystemExit):
            cli.cli(
                ["load", *files, "--parallel", "-d", "-L", server.socket_name],
            )
        for session_name, panes in case.sessions:
            built = server.sessions.get(session_name=session_name, default=None)
            assert built is not None
            assert len(built.windows[0].panes) == len(panes)
    finally:
        _kill(server, *names)


def test_parallel_dry_run_does_not_build(
    server: Server,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--dry-run`` prints the compiled plan and touches no tmux server."""
    assert server.socket_name is not None
    cfg = tmp_path / "ws.yaml"
    _write_workspace(cfg, "ppar-dry", ["echo a", "echo b"])
    with contextlib.suppress(SystemExit):
        cli.cli(
            ["load", str(cfg), "--parallel", "--dry-run", "-L", server.socket_name],
        )
    out = capsys.readouterr().out
    assert "[Dry run]" in out
    assert "new-session" in out
    assert server.sessions.get(session_name="ppar-dry", default=None) is None


def test_parallel_rejects_duplicate_names(
    server: Server,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Two workspaces with the same session name are unbuildable."""
    assert server.socket_name is not None
    cfg = tmp_path / "ws.yaml"
    _write_workspace(cfg, "ppar-dup", ["echo a"])
    try:
        with contextlib.suppress(SystemExit):
            cli.cli(
                [
                    "load",
                    str(cfg),
                    str(cfg),
                    "--parallel",
                    "-d",
                    "-L",
                    server.socket_name,
                ],
            )
        out = capsys.readouterr().out
        assert "duplicate sessions" in out
        assert server.sessions.get(session_name="ppar-dup", default=None) is None
    finally:
        _kill(server, "ppar-dup")


@pytest.mark.parametrize("flag", ["--dry-run", "--no-fold"])
def test_dry_run_and_no_fold_require_parallel(
    flag: str,
    server: Server,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--dry-run``/``--no-fold`` without ``--parallel`` fail instead of building."""
    assert server.socket_name is not None
    cfg = tmp_path / "ws.yaml"
    _write_workspace(cfg, "ppar-guard", ["echo a"])
    try:
        with contextlib.suppress(SystemExit):
            cli.cli(["load", str(cfg), flag, "-d", "-L", server.socket_name])
        out = capsys.readouterr().out
        assert "require --parallel" in out
        assert server.sessions.get(session_name="ppar-guard", default=None) is None
    finally:
        _kill(server, "ppar-guard")


class _RejectCase(t.NamedTuple):
    """An incompatible flag and the phrase its rejection must mention."""

    test_id: str
    extra_args: list[str]
    needle: str


_REJECT_CASES: tuple[_RejectCase, ...] = (
    _RejectCase(test_id="append", extra_args=["-a"], needle="--append"),
    _RejectCase(test_id="new_session_name", extra_args=["-s", "renamed"], needle="-s"),
)


@pytest.mark.parametrize(
    "case",
    _REJECT_CASES,
    ids=[c.test_id for c in _REJECT_CASES],
)
def test_parallel_rejects_incompatible_flags(
    case: _RejectCase,
    server: Server,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--parallel`` refuses single-session flags before touching tmux."""
    assert server.socket_name is not None
    cfg = tmp_path / "ws.yaml"
    _write_workspace(cfg, "ppar-reject", ["echo a"])
    try:
        with contextlib.suppress(SystemExit):
            cli.cli(
                [
                    "load",
                    str(cfg),
                    "--parallel",
                    "-d",
                    "-L",
                    server.socket_name,
                    *case.extra_args,
                ],
            )
        out = capsys.readouterr().out
        assert case.needle in out
        assert server.sessions.get(session_name="ppar-reject", default=None) is None
    finally:
        _kill(server, "ppar-reject")
