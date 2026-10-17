"""Optional-feature command policy before custom workspace code."""

from __future__ import annotations

import json
import pathlib
import re
import shlex
import typing as t
import uuid

import pytest
from libtmux._internal import support
from libtmux.exc import LibTmuxException
from libtmux.server import Server
from libtmux.session import Session

from tmuxp import cli, exc
from tmuxp.cli import load
from tmuxp.workspace import freezer


@pytest.mark.parametrize("kind", ["builder", "plugin"])
def test_backend_without_command_policy_refuses_before_import(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    """A libtmux that cannot check literal commands cannot run custom code."""
    monkeypatch.delattr(support, "require_commands")
    effect = tmp_path / "imported"
    module = "tmuxp_policy_" + uuid.uuid4().hex
    (tmp_path / f"{module}.py").write_text(
        f"from pathlib import Path\nPath({str(effect)!r}).touch()\n"
    )
    config: dict[str, t.Any] = {
        "session_name": "policy",
        "windows": [{"panes": ["true"]}],
    }
    if kind == "builder":
        config.update(
            workspace_builder=f"{module}:Builder",
            workspace_builder_paths=[str(tmp_path)],
        )
    else:
        monkeypatch.syspath_prepend(str(tmp_path))
        config["plugins"] = [f"{module}.Plugin"]
    path = tmp_path / "workspace.json"
    path.write_text(json.dumps(config))
    with pytest.raises(exc.LibtmuxCompatibilityError, match=r"libtmux 0\.63"):
        load.load_workspace(path, detached=True)
    assert not effect.exists()


def test_backend_without_command_policy_refuses_shell_code(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Refuse a shell command before it can execute custom Python."""
    monkeypatch.delattr(support, "require_commands")
    effect = tmp_path / "executed"
    command = f"from pathlib import Path; Path({str(effect)!r}).touch()"
    with pytest.raises(SystemExit) as error:
        cli.cli(["shell", "-c", command])
    assert error.value.code == 1
    assert not effect.exists()
    output = capsys.readouterr()
    assert "libtmux 0.63" in output.out
    assert "Traceback" not in output.err


def test_ordinary_workspace_and_percentage_split(
    tmp_path: pathlib.Path, server: Server
) -> None:
    """Keep ordinary workspaces and portable percentage splitting available."""
    config = tmp_path / "ordinary.json"
    config.write_text(
        json.dumps(
            {
                "session_name": "ordinary",
                "windows": [{"layout": "even-horizontal", "panes": ["true", "true"]}],
            }
        )
    )
    session = load.load_workspace(
        config, socket_name=server.socket_name, detached=True, no_progress=True
    )
    assert session is not None
    window = session.active_window
    assert len(window.panes) == 2
    pane = window.active_pane
    assert pane is not None
    assert pane.pane_height is not None
    original_height = int(pane.pane_height)
    split = pane.split(percentage=30)
    assert split.pane_height is not None
    assert abs(int(split.pane_height) - original_height * 0.3) <= 2
    assert len(window.panes) == 3
    assert isinstance(split.capture_pane(), list)
    frozen = freezer.freeze(session)
    assert frozen["session_name"] == "ordinary"
    assert len(frozen["windows"][0]["panes"]) == 3


def test_serialized_workspace_layout_remains_available(
    tmp_path: pathlib.Path, server: Server, session: Session
) -> None:
    """Load and freeze a workspace with a native serialized layout."""
    layout = session.active_window.window_layout
    assert layout is not None
    config = tmp_path / "serialized.json"
    config.write_text(
        json.dumps(
            {
                "session_name": "serialized",
                "windows": [{"layout": layout, "panes": ["true"]}],
            }
        )
    )
    loaded = load.load_workspace(
        config, socket_name=server.socket_name, detached=True, no_progress=True
    )
    assert loaded is not None
    assert len(loaded.active_window.panes) == 1
    pane = loaded.active_window.active_pane
    assert pane is not None
    assert isinstance(pane.capture_pane(), list)
    frozen = freezer.freeze(loaded)
    assert frozen["windows"][0]["layout"] == loaded.active_window.window_layout


def test_invalid_workspace_layout_preserves_running_sessions(
    tmp_path: pathlib.Path, server: Server, session: Session
) -> None:
    """A bad layout cannot terminate the daemon or send the pane command."""
    effect = tmp_path / "pane-command"
    config = tmp_path / "invalid-layout.json"
    config.write_text(
        json.dumps(
            {
                "session_name": "invalid-layout",
                "windows": [
                    {
                        "layout": "not-a-layout",
                        "panes": [f"touch {shlex.quote(str(effect))}"],
                    }
                ],
            }
        )
    )
    with pytest.raises(LibTmuxException, match="layout"):
        load.load_workspace(
            config, socket_name=server.socket_name, detached=True, no_progress=True
        )
    assert not effect.exists()
    assert session.name is not None
    assert server.has_session(session.name)
    assert session.active_window.panes


def test_shell_named_buffer_policy(
    server: Server, session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    """A shell uses the backend's exact named-buffer requirement."""
    socket_name = server.socket_name
    session_name = session.name
    assert socket_name is not None and session_name is not None
    name = "tmuxp_feature_" + uuid.uuid4().hex
    server.set_buffer("retained", buffer_name=name)
    argv = [
        "shell",
        "-L",
        socket_name,
        session_name,
        "-c",
        f"server.delete_buffer(buffer_name={name!r})",
    ]
    if server._get_version() == "3.3a":
        with pytest.raises(SystemExit) as error:
            cli.cli(argv)
        assert error.value.code == 1
        assert "3.4" in capsys.readouterr().out
        assert server.show_buffer(buffer_name=name) == "retained"
    else:
        cli.cli(argv)
        remaining = server.cmd("list-buffers", "-F", "#{buffer_name}")
        assert name not in remaining.stdout


def test_shell_captured_job_policy(
    tmp_path: pathlib.Path,
    server: Server,
    session: Session,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Refuse unavailable captured output before starting the shell job."""
    socket_name = server.socket_name
    session_name = session.name
    assert socket_name is not None and session_name is not None
    effect = tmp_path / "job-executed"
    command = f"printf tmuxp-feature; touch {shlex.quote(str(effect))}"
    argv = [
        "shell",
        "-L",
        socket_name,
        session_name,
        "-c",
        f"assert server.run_shell({command!r}) == ['tmuxp-feature']",
    ]
    if server._get_version() in {"3.3a", "3.4"}:
        with pytest.raises(SystemExit) as error:
            cli.cli(argv)
        assert error.value.code == 1
        assert "3.5" in capsys.readouterr().out
        assert not effect.exists()
    else:
        cli.cli(argv)
        assert effect.exists()


def test_shell_control_acquisition_policy(
    server: Server, session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    """Apply the control-client requirement inside a tmuxp shell."""
    socket_name = server.socket_name
    session_name = session.name
    assert socket_name is not None and session_name is not None
    command = (
        "from libtmux._internal.control_mode import ControlMode\n"
        "with ControlMode(server=server, session=session) as client:\n"
        "    assert client.client_name\n"
    )
    argv = ["shell", "-L", socket_name, session_name, "-c", command]
    version = server._get_version()
    release = re.fullmatch(r"(\d+)\.(\d+)[a-z]?", version)
    if release is None or tuple(map(int, release.groups())) < (3, 7):
        with pytest.raises(SystemExit) as error:
            cli.cli(argv)
        assert error.value.code == 1
        assert "ControlMode" in capsys.readouterr().out
        assert not server.list_clients()
    else:
        cli.cli(argv)
    assert server.has_session(session_name)


def test_shell_break_policy(
    server: Server, session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    """Keep a named break available and refuse an unsafe exact-3.7 break."""
    socket_name = server.socket_name
    session_name = session.name
    assert socket_name is not None and session_name is not None
    source = session.active_window
    pane = source.active_pane
    assert pane is not None
    pane.split()
    argv = ["shell", "-L", socket_name, session_name, "-c"]
    if server._get_version() == "3.7":
        panes = {item.pane_id for item in source.panes}
        with pytest.raises(SystemExit) as error:
            cli.cli([*argv, "pane.break_pane()"])
        assert error.value.code == 1
        assert "window_name" in capsys.readouterr().out
        assert len(session.windows) == 1
        assert {item.pane_id for item in source.panes} == panes
    command = (
        "result = pane.break_pane(window_name='tmuxp-break'); "
        "assert result.window_name == 'tmuxp-break'"
    )
    cli.cli([*argv, command])
    assert len(session.windows) == 2
    assert session.windows.get(window_name="tmuxp-break") is not None
