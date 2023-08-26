import contextlib
import io
import pathlib
import subprocess
import typing as t

import pytest
from libtmux.server import Server
from libtmux.session import Session

from tmuxp import cli, exc


@pytest.mark.parametrize("cli_cmd", [["shell"], ["shell", "--pdb"]])
@pytest.mark.parametrize(
    "cli_args,inputs,env,expected_output",
    [
        (
            ["-L{SOCKET_NAME}", "-c", "print(str(server.socket_name))"],
            [],
            {},
            "{SERVER_SOCKET_NAME}",
        ),
        (
            [
                "-L{SOCKET_NAME}",
                "{SESSION_NAME}",
                "-c",
                "print(session.name)",
            ],
            [],
            {},
            "{SESSION_NAME}",
        ),
        (
            [
                "-L{SOCKET_NAME}",
                "{SESSION_NAME}",
                "{WINDOW_NAME}",
                "-c",
                "print(server.has_session(session.name))",
            ],
            [],
            {},
            "True",
        ),
        (
            [
                "-L{SOCKET_NAME}",
                "{SESSION_NAME}",
                "{WINDOW_NAME}",
                "-c",
                "print(window.name)",
            ],
            [],
            {},
            "{WINDOW_NAME}",
        ),
        (
            [
                "-L{SOCKET_NAME}",
                "{SESSION_NAME}",
                "{WINDOW_NAME}",
                "-c",
                "print(pane.id)",
            ],
            [],
            {},
            "{PANE_ID}",
        ),
        (
            [
                "-L{SOCKET_NAME}",
                "-c",
                "print(pane.id)",
            ],
            [],
            {"TMUX_PANE": "{PANE_ID}"},
            "{PANE_ID}",
        ),
    ],
)
def test_shell(
    cli_cmd: t.List[str],
    cli_args: t.List[str],
    inputs: t.List[t.Any],
    expected_output: str,
    env: t.Dict[str, str],
    server: "Server",
    session: Session,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    window_name = "my_window"
    window = session.new_window(window_name=window_name)
    window.split_window()

    assert window.attached_pane is not None

    template_ctx = {
        "SOCKET_NAME": server.socket_name,
        "SESSION_NAME": session.name,
        "WINDOW_NAME": window_name,
        "PANE_ID": window.attached_pane.id,
        "SERVER_SOCKET_NAME": server.socket_name,
    }

    cli_args = cli_cmd + [cli_arg.format(**template_ctx) for cli_arg in cli_args]

    for k, v in env.items():
        monkeypatch.setenv(k, v.format(**template_ctx))

    monkeypatch.chdir(tmp_path)

    cli.cli(cli_args)
    result = capsys.readouterr()
    assert expected_output.format(**template_ctx) in result.out


@pytest.mark.parametrize(
    "cli_cmd",
    [
        ["shell"],
        ["shell", "--pdb"],
    ],
)
@pytest.mark.parametrize(
    "cli_args,inputs,env,template_ctx,exception,message",
    [
        (
            ["-LDoesNotExist", "-c", "print(str(server.socket_name))"],
            [],
            {},
            {},
            subprocess.CalledProcessError,
            r".*DoesNotExist.*",
        ),
        (
            [
                "-L{SOCKET_NAME}",
                "nonexistent_session",
                "-c",
                "print(str(server.socket_name))",
            ],
            [],
            {},
            {"session_name": "nonexistent_session"},
            exc.TmuxpException,
            "Session not found: nonexistent_session",
        ),
        (
            [
                "-L{SOCKET_NAME}",
                "{SESSION_NAME}",
                "nonexistent_window",
                "-c",
                "print(str(server.socket_name))",
            ],
            [],
            {},
            {"window_name": "nonexistent_window"},
            exc.TmuxpException,
            "Window not found: {WINDOW_NAME}",
        ),
    ],
)
def test_shell_target_missing(
    cli_cmd: t.List[str],
    cli_args: t.List[str],
    inputs: t.List[t.Any],
    env: t.Dict[t.Any, t.Any],
    template_ctx: t.Dict[str, str],
    exception: t.Union[
        t.Type[exc.TmuxpException], t.Type[subprocess.CalledProcessError]
    ],
    message: str,
    socket_name: str,
    server: "Server",
    session: Session,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    window_name = "my_window"
    window = session.new_window(window_name=window_name)
    window.split_window()

    assert server.socket_name is not None
    assert session.name is not None

    template_ctx.update(
        {
            "SOCKET_NAME": server.socket_name,
            "SESSION_NAME": session.name,
            "WINDOW_NAME": template_ctx.get("window_name", window_name),
        }
    )
    cli_args = cli_cmd + [cli_arg.format(**template_ctx) for cli_arg in cli_args]

    for k, v in env.items():
        monkeypatch.setenv(k, v.format(**template_ctx))

    monkeypatch.chdir(tmp_path)

    if exception is not None:
        with pytest.raises(exception, match=message.format(**template_ctx)):
            cli.cli(cli_args)
    else:
        cli.cli(cli_args)
        result = capsys.readouterr()
        assert message.format(**template_ctx) in result.out


@pytest.mark.parametrize(
    "cli_cmd",
    [
        # ['shell'],
        # ['shell', '--pdb'),
        ["shell", "--code"],
        # ['shell', '--bpython'],
        # ['shell', '--ptipython'],
        # ['shell', '--ptpython'],
        # ['shell', '--ipython'],
    ],
)
@pytest.mark.parametrize(
    "cli_args,inputs,env,message",
    [
        (
            [
                "-L{SOCKET_NAME}",
            ],
            [],
            {},
            "(InteractiveConsole)",
        ),
        (
            [
                "-L{SOCKET_NAME}",
            ],
            [],
            {"PANE_ID": "{PANE_ID}"},
            "(InteractiveConsole)",
        ),
    ],
)
def test_shell_interactive(
    cli_cmd: t.List[str],
    cli_args: t.List[str],
    inputs: t.List[t.Any],
    env: t.Dict[str, str],
    message: str,
    server: "Server",
    session: Session,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    window_name = "my_window"
    window = session.new_window(window_name=window_name)
    window.split_window()

    assert window.attached_pane is not None

    template_ctx = {
        "SOCKET_NAME": server.socket_name,
        "SESSION_NAME": session.name,
        "WINDOW_NAME": window_name,
        "PANE_ID": window.attached_pane.id,
        "SERVER_SOCKET_NAME": server.socket_name,
    }

    cli_args = cli_cmd + [cli_arg.format(**template_ctx) for cli_arg in cli_args]

    for k, v in env.items():
        monkeypatch.setenv(k, v.format(**template_ctx))

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("exit()\r"))
    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    result = capsys.readouterr()
    assert message.format(**template_ctx) in result.err
