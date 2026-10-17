"""Version checks before workspace imports, callbacks, and shell setup."""

from __future__ import annotations

import importlib
import json
import os
import pathlib
import subprocess
import types
import typing as t
import uuid

import pytest
from libtmux.exc import VersionTooLow
from libtmux.server import Server
from libtmux.session import Session
from libtmux.window import Window

from tmuxp import cli, exc
from tmuxp.cli import load, shell
from tmuxp.workspace import freezer, loader
from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder

if t.TYPE_CHECKING:
    from collections.abc import Iterator


def _native(binary: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [binary, *args], capture_output=True, text=True, timeout=5, check=False
    )


@pytest.fixture
def unsupported_tmux() -> str:
    """Use an explicitly supplied tmux below the core floor."""
    binary = os.environ.get("TMUXP_TEST_OLD_TMUX")
    if not binary:
        pytest.skip("set TMUXP_TEST_OLD_TMUX to test an unsupported tmux")
    report = _native(binary, "-V")
    assert report.returncode == 0
    assert report.stdout.strip().endswith((" 3.2a", " 3.3"))
    return binary


@pytest.fixture
def unsupported_endpoint(unsupported_tmux: str) -> Iterator[str]:
    """Keep an old daemon alive while the configured client is supported."""
    name = "tmuxp_versions_" + uuid.uuid4().hex
    started = _native(
        unsupported_tmux,
        "-f",
        "/dev/null",
        "-L",
        name,
        "new-session",
        "-d",
        "-s",
        "old",
    )
    assert started.returncode == 0, started.stderr
    try:
        yield name
    finally:
        _native(unsupported_tmux, "-L", name, "kill-server")


def _workspace(tmp_path: pathlib.Path, **extra: t.Any) -> pathlib.Path:
    config: dict[str, t.Any] = {
        "session_name": "checked",
        "windows": [{"window_name": "main", "panes": ["true"]}],
        **extra,
    }
    path = tmp_path / "workspace.json"
    path.write_text(json.dumps(config))
    return path


@pytest.mark.parametrize("kind", ["builder", "plugin"])
def test_unsupported_endpoint_refuses_before_import(
    tmp_path: pathlib.Path,
    unsupported_endpoint: str,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    """A modern client cannot authorize imports on an older selected daemon."""
    marker = tmp_path / "imported"
    module = "tmuxp_versions_" + uuid.uuid4().hex
    body = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).touch()\n"
        "from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder\n"
        "class Plugin:\n    pass\n"
    )
    (tmp_path / f"{module}.py").write_text(body)
    if kind == "builder":
        path = _workspace(
            tmp_path,
            workspace_builder=f"{module}:ClassicWorkspaceBuilder",
            workspace_builder_paths=[str(tmp_path)],
        )
    else:
        monkeypatch.syspath_prepend(str(tmp_path))
        path = _workspace(tmp_path, plugins=[f"{module}.Plugin"])
    with pytest.raises(VersionTooLow, match=r"3\.3a"):
        load.load_workspace(path, socket_name=unsupported_endpoint, detached=True)
    assert not marker.exists()


def test_unsupported_cold_endpoint_refuses_before_import(
    tmp_path: pathlib.Path,
    unsupported_tmux: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An old cold executable cannot authorize builder imports or start tmux."""
    monkeypatch.setenv("PATH", str(pathlib.Path(unsupported_tmux).parent))
    marker = tmp_path / "imported"
    module = "tmuxp_versions_" + uuid.uuid4().hex
    (tmp_path / f"{module}.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
    )
    path = _workspace(
        tmp_path,
        workspace_builder=f"{module}:Builder",
        workspace_builder_paths=[str(tmp_path)],
    )
    name = "tmuxp_cold_" + uuid.uuid4().hex
    with pytest.raises(VersionTooLow, match=r"3\.3a"):
        load.load_workspace(path, socket_name=name, detached=True)
    assert not marker.exists()
    assert _native(unsupported_tmux, "-N", "-L", name, "list-sessions").returncode


def test_unsupported_cli_reports_a_nonzero_error(
    tmp_path: pathlib.Path,
    unsupported_endpoint: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Render version errors through the CLI without a traceback."""
    path = _workspace(tmp_path)
    with pytest.raises(SystemExit) as error:
        cli.cli(["load", "-L", unsupported_endpoint, "-d", str(path)])
    assert error.value.code == 1
    output = capsys.readouterr()
    assert "[Tmux Error]" in output.out
    assert "3.3a" in output.out
    assert "Traceback" not in output.err


def test_unsupported_diagnostics_remains_available(
    unsupported_tmux: str,
    unsupported_endpoint: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Report an unsupported selected daemon without changing its state."""
    endpoint = _native(
        unsupported_tmux,
        "-L",
        unsupported_endpoint,
        "display-message",
        "-p",
        "#{socket_path},#{pid},0",
    )
    assert endpoint.returncode == 0
    monkeypatch.setenv("TMUX", endpoint.stdout.strip())
    cli.cli(["debug-info", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert not any(data["tmux"].values())
    assert all("3.3a" in message for message in data["tmux_errors"].values())
    sessions = _native(unsupported_tmux, "-L", unsupported_endpoint, "list-sessions")
    assert sessions.returncode == 0 and "old:" in sessions.stdout


@pytest.mark.parametrize("mode", ["command", "startup"])
def test_unsupported_endpoint_refuses_shell_setup(
    tmp_path: pathlib.Path,
    unsupported_endpoint: str,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    """Refuse before command execution, Python startup, or shell imports."""
    marker = tmp_path / "executed"
    code = f"from pathlib import Path; Path({str(marker)!r}).touch()"
    argv = ["shell", "-L", unsupported_endpoint]
    if mode == "command":
        argv += ["-c", code]
    else:
        startup = tmp_path / "startup.py"
        startup.write_text(code)
        monkeypatch.setenv("PYTHONSTARTUP", str(startup))
        argv += ["--code", "--use-pythonrc"]
    args = cli.create_parser().parse_args(argv, namespace=shell.CLIShellNamespace())
    with pytest.raises(VersionTooLow, match=r"3\.3a"):
        shell.command_shell(args)
    assert not marker.exists()


@pytest.mark.parametrize("entry", ["build", "windows", "panes", "options", "freeze"])
def test_unsupported_supplied_target_refuses_before_callback(
    server: Server,
    unsupported_endpoint: str,
    entry: str,
) -> None:
    """A supplied session or window selects its own daemon before callbacks."""
    config = loader.trickle(
        loader.expand({"session_name": "requested", "windows": [{"panes": ["true"]}]})
    )
    calls: list[str] = []
    builder = ClassicWorkspaceBuilder(config, server, on_progress=calls.append)
    old_server = Server(socket_name=unsupported_endpoint)
    session = Session(server=old_server, session_id="$0", session_name="old")
    window = Window(server=old_server, session_id="$0", window_id="@0")
    with pytest.raises(VersionTooLow, match=r"3\.3a"):
        if entry == "build":
            builder.build(session=session)
        elif entry == "windows":
            next(builder.iter_create_windows(session))
        elif entry == "panes":
            next(builder.iter_create_panes(window, config["windows"][0]))
        elif entry == "options":
            builder.config_after_window(window, {"options_after": {"@effect": "yes"}})
        else:
            freezer.freeze(session)
    assert not calls


def test_builder_checks_a_server_once(
    server: Server, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Window, pane and option hooks reuse the version check made for the build."""
    checked: list[Server] = []
    monkeypatch.setattr("tmuxp.workspace.builder.classic._require_tmux", checked.append)
    config = loader.trickle(
        loader.expand(
            {
                "session_name": "check-once",
                "windows": [
                    {"window_name": "one", "panes": ["true", "true"]},
                    {"window_name": "two", "panes": ["true"]},
                ],
            }
        )
    )
    builder = ClassicWorkspaceBuilder(config, server)
    builder.build()
    assert checked == [server]


def test_missing_backend_refuses_before_import(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refuse a libtmux without a version check before resolving custom builders."""
    original = importlib.import_module
    calls: list[str] = []

    def import_module(name: str, package: str | None = None) -> types.ModuleType:
        calls.append(name)
        if name == "libtmux._internal.support":
            return types.ModuleType(name)
        return original(name, package)

    monkeypatch.setattr(importlib, "import_module", import_module)
    path = _workspace(tmp_path, workspace_builder="not_imported:Builder")
    with pytest.raises(exc.TmuxpException, match=r"libtmux 0\.63"):
        load.load_workspace(path, detached=True)
    assert "not_imported" not in calls


@pytest.mark.parametrize("argv", [["--help"], ["--version"], ["debug-info", "--json"]])
def test_diagnostics_without_tmux(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    """Help, version, and diagnostics do not need a checked endpoint."""
    monkeypatch.setenv("PATH", str(tmp_path))
    try:
        cli.cli(argv)
    except SystemExit as error:
        assert error.code == 0
    output = capsys.readouterr().out
    if argv == ["--help"]:
        assert "usage: tmuxp" in output
    elif argv == ["--version"]:
        assert "tmuxp " in output and "libtmux " in output
    else:
        data = json.loads(output)
        assert data["tmux_version"] == "not found"
        assert not any(data["tmux"].values())
        assert data["tmux_errors"]["sessions"] == "tmux executable not found"


def test_convert_without_tmux(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Configuration conversion remains available with tmux absent."""
    path = _workspace(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    cli.cli(["convert", "-y", str(path)])
    assert path.with_suffix(".yaml").exists()


def test_missing_tmux_cli_explains_the_error(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Explain a missing executable while retaining a failing exit status."""
    path = _workspace(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(SystemExit) as error:
        cli.cli(["load", "-d", str(path)])
    assert error.value.code == 1
    output = capsys.readouterr()
    assert "tmux executable not found" in output.out
    assert "Traceback" not in output.err


def test_supported_workspace_builds_and_captures(
    tmp_path: pathlib.Path, server: Server
) -> None:
    """Build an ordinary workspace through the installed libtmux dependency."""
    path = _workspace(tmp_path)
    session = load.load_workspace(
        path, socket_name=server.socket_name, detached=True, no_progress=True
    )
    assert session is not None
    assert session.name == "checked"
    assert session.active_window.name == "main"
    pane = session.active_window.active_pane
    assert pane is not None
    assert isinstance(pane.capture_pane(), list)
