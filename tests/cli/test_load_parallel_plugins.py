"""Plugin-hook behavior on the engine-ops set-build path (--parallel/--expand)."""

from __future__ import annotations

import contextlib
import logging
import typing as t

import pytest

from tmuxp import cli

if t.TYPE_CHECKING:
    import pathlib

    from libtmux.server import Server

_BS = "tmuxp_test_plugin_bs.plugin.PluginBeforeScript"
_BWB = "tmuxp_test_plugin_bwb.plugin.PluginBeforeWorkspaceBuilder"
_OWC = "tmuxp_test_plugin_owc.plugin.PluginOnWindowCreate"
_AWF = "tmuxp_test_plugin_awf.plugin.PluginAfterWindowFinished"


def _kill(server: Server, *session_names: str) -> None:
    """Kill each named session if present, leaving the server clean."""
    for name in session_names:
        with contextlib.suppress(Exception):
            sess = server.sessions.get(session_name=name, default=None)
            if sess is not None:
                sess.kill()


def _skip_warnings(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    """Return the mid-build-hook skip warnings captured so far."""
    return [r for r in caplog.records if getattr(r, "skipped_hooks", None)]


class _HookCase(t.NamedTuple):
    """A plugin, the set flag, and the hook behavior it should exhibit."""

    test_id: str
    dotted: str
    flag_args: list[str]
    declared_name: str
    expect_session: str
    warn_hook: str | None
    cleanup: tuple[str, ...]


_HOOK_CASES: tuple[_HookCase, ...] = (
    _HookCase(
        test_id="before_script_parallel_runs",
        dotted=_BS,
        flag_args=["--parallel"],
        declared_name="plug-bs",
        expect_session="plugin_test_bs",  # renamed by before_script
        warn_hook=None,
        cleanup=("plug-bs", "plugin_test_bs"),
    ),
    _HookCase(
        test_id="before_script_expand_runs",
        dotted=_BS,
        flag_args=["--expand", "n=solo"],
        declared_name="plug-$n",
        expect_session="plugin_test_bs",
        warn_hook=None,
        cleanup=("plug-solo", "plugin_test_bs"),
    ),
    _HookCase(
        test_id="before_workspace_builder_warns",
        dotted=_BWB,
        flag_args=["--parallel"],
        declared_name="plug-bwb",
        expect_session="plug-bwb",  # NOT renamed: mid-build hook skipped
        warn_hook="before_workspace_builder",
        cleanup=("plug-bwb",),
    ),
    _HookCase(
        test_id="on_window_create_warns",
        dotted=_OWC,
        flag_args=["--parallel"],
        declared_name="plug-owc",
        expect_session="plug-owc",
        warn_hook="on_window_create",
        cleanup=("plug-owc",),
    ),
    _HookCase(
        test_id="after_window_finished_warns",
        dotted=_AWF,
        flag_args=["--parallel"],
        declared_name="plug-awf",
        expect_session="plug-awf",
        warn_hook="after_window_finished",
        cleanup=("plug-awf",),
    ),
)


@pytest.mark.usefixtures("monkeypatch_plugin_test_packages")
@pytest.mark.parametrize("case", _HOOK_CASES, ids=[c.test_id for c in _HOOK_CASES])
def test_set_path_plugin_hooks(
    case: _HookCase,
    server: Server,
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Post-build before_script runs; mid-build hooks warn and skip."""
    assert server.socket_name is not None
    cfg = tmp_path / "ws.yaml"
    cfg.write_text(
        f"session_name: {case.declared_name}\n"
        f"plugins:\n- '{case.dotted}'\n"
        "windows:\n- panes: [echo a]\n",
        encoding="utf-8",
    )
    try:
        with (
            caplog.at_level(logging.WARNING, logger="tmuxp.cli.load"),
            contextlib.suppress(SystemExit),
        ):
            cli.cli(["load", str(cfg), *case.flag_args, "-d", "-L", server.socket_name])
        assert server.sessions.get(session_name=case.expect_session, default=None)
        warns = _skip_warnings(caplog)
        if case.warn_hook is None:
            assert warns == []
        else:
            assert any(case.warn_hook in getattr(r, "skipped_hooks", "") for r in warns)
            assert all(getattr(r, "plugin", None) for r in warns)
    finally:
        _kill(server, *case.cleanup)


def test_set_path_before_script_raise_is_lenient(
    server: Server,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A before_script that raises is logged and skipped, not fatal to the set."""
    assert server.socket_name is not None
    (tmp_path / "raising_plugin.py").write_text(
        "from __future__ import annotations\n\n"
        "from tmuxp.plugin import TmuxpPlugin\n\n\n"
        "class Boom(TmuxpPlugin):\n"
        "    def __init__(self) -> None:\n"
        "        pass\n\n"
        "    def before_script(self, session) -> None:\n"
        "        raise RuntimeError('boom')\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    cfg = tmp_path / "ws.yaml"
    cfg.write_text(
        "session_name: boom-a\n"
        "plugins:\n- 'raising_plugin.Boom'\n"
        "windows:\n- panes: [echo a]\n",
        encoding="utf-8",
    )
    try:
        with (
            caplog.at_level(logging.WARNING, logger="tmuxp.cli.load"),
            contextlib.suppress(SystemExit),
        ):
            cli.cli(["load", str(cfg), "--parallel", "-d", "-L", server.socket_name])
        # The build survived the raising hook.
        assert server.sessions.get(session_name="boom-a", default=None)
        assert any("before_script failed" in r.getMessage() for r in caplog.records)
    finally:
        _kill(server, "boom-a")


def test_set_path_no_plugins_skips_loading(
    server: Server,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A plugin-free set build never calls load_plugins."""
    assert server.socket_name is not None
    calls: list[dict[str, t.Any]] = []
    from tmuxp.cli import load as load_module

    real = load_module.load_plugins

    def _spy(
        session_config: dict[str, t.Any],
        colors: t.Any = None,
    ) -> list[t.Any]:
        calls.append(session_config)
        return real(session_config, colors)

    monkeypatch.setattr(load_module, "load_plugins", _spy)
    cfg = tmp_path / "ws.yaml"
    cfg.write_text(
        "session_name: noplug-a\nwindows:\n- panes: [echo a]\n",
        encoding="utf-8",
    )
    try:
        with contextlib.suppress(SystemExit):
            cli.cli(["load", str(cfg), "--parallel", "-d", "-L", server.socket_name])
        assert server.sessions.get(session_name="noplug-a", default=None)
        assert calls == []
    finally:
        _kill(server, "noplug-a")
