"""CLI tests for tmuxp shell."""

import contextlib
import io
import pathlib
import subprocess
import typing as t

import pytest
from libtmux.session import Session

from tmuxp import cli, exc

if t.TYPE_CHECKING:
    from libtmux.server import Server


class CLIShellFixture(t.NamedTuple):
    """Test fixture for tmuxp shell tests."""

    # pytest (internal): Test fixture name
    test_id: str

    # test params
    cli_args: t.List[str]
    inputs: t.List[t.Any]
    env: t.Dict[str, str]
    expected_output: str


TEST_SHELL_FIXTURES: t.List[CLIShellFixture] = [
    CLIShellFixture(
        test_id="print-socket-name",
        cli_args=["-L{SOCKET_NAME}", "-c", "print(str(server.socket_name))"],
        inputs=[],
        env={},
        expected_output="{SERVER_SOCKET_NAME}",
    ),
    CLIShellFixture(
        test_id="print-session-name",
        cli_args=[
            "-L{SOCKET_NAME}",
            "{SESSION_NAME}",
            "-c",
            "print(session.name)",
        ],
        inputs=[],
        env={},
        expected_output="{SESSION_NAME}",
    ),
    CLIShellFixture(
        test_id="print-has-session",
        cli_args=[
            "-L{SOCKET_NAME}",
            "{SESSION_NAME}",
            "{WINDOW_NAME}",
            "-c",
            "print(server.has_session(session.name))",
        ],
        inputs=[],
        env={},
        expected_output="True",
    ),
    CLIShellFixture(
        test_id="print-window-name",
        cli_args=[
            "-L{SOCKET_NAME}",
            "{SESSION_NAME}",
            "{WINDOW_NAME}",
            "-c",
            "print(window.name)",
        ],
        inputs=[],
        env={},
        expected_output="{WINDOW_NAME}",
    ),
    CLIShellFixture(
        test_id="print-pane-id",
        cli_args=[
            "-L{SOCKET_NAME}",
            "{SESSION_NAME}",
            "{WINDOW_NAME}",
            "-c",
            "print(pane.id)",
        ],
        inputs=[],
        env={},
        expected_output="{PANE_ID}",
    ),
    CLIShellFixture(
        test_id="print-pane-id-obeys-tmux-pane-env-var",
        cli_args=[
            "-L{SOCKET_NAME}",
            "-c",
            "print(pane.id)",
        ],
        inputs=[],
        env={"TMUX_PANE": "{PANE_ID}"},
        expected_output="{PANE_ID}",
    ),
]


@pytest.mark.parametrize("cli_cmd", [["shell"], ["shell", "--pdb"]])
@pytest.mark.parametrize(
    list(CLIShellFixture._fields),
    TEST_SHELL_FIXTURES,
    ids=[test.test_id for test in TEST_SHELL_FIXTURES],
)
def test_shell(
    cli_cmd: t.List[str],
    test_id: str,
    cli_args: t.List[str],
    inputs: t.List[t.Any],
    env: t.Dict[str, str],
    expected_output: str,
    server: "Server",
    session: Session,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI tests for tmuxp shell."""
    monkeypatch.setenv("HOME", str(tmp_path))
    window_name = "my_window"
    window = session.new_window(window_name=window_name)
    window.split()

    assert window.active_pane is not None

    template_ctx = {
        "SOCKET_NAME": server.socket_name,
        "SESSION_NAME": session.name,
        "WINDOW_NAME": window_name,
        "PANE_ID": window.active_pane.id,
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
    ("cli_args", "inputs", "env", "template_ctx", "exception", "message"),
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
        t.Type[exc.TmuxpException],
        t.Type[subprocess.CalledProcessError],
    ],
    message: str,
    socket_name: str,
    server: "Server",
    session: Session,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI tests for tmuxp shell when target is not specified."""
    monkeypatch.setenv("HOME", str(tmp_path))
    window_name = "my_window"
    window = session.new_window(window_name=window_name)
    window.split()

    assert server.socket_name is not None
    assert session.name is not None

    template_ctx.update(
        {
            "SOCKET_NAME": server.socket_name,
            "SESSION_NAME": session.name,
            "WINDOW_NAME": template_ctx.get("window_name", window_name),
        },
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
    ("cli_args", "inputs", "env", "message"),
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
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI tests for tmuxp shell when shell is specified."""
    monkeypatch.setenv("HOME", str(tmp_path))
    window_name = "my_window"
    window = session.new_window(window_name=window_name)
    window.split()

    assert window.active_pane is not None

    template_ctx = {
        "SOCKET_NAME": server.socket_name,
        "SESSION_NAME": session.name,
        "WINDOW_NAME": window_name,
        "PANE_ID": window.active_pane.id,
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
