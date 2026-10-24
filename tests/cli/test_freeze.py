"""Test workspace freezing functionality for tmuxp."""

from __future__ import annotations

import contextlib
import io
import typing as t

import pytest

from tmuxp import cli
from tmuxp._internal.config_reader import ConfigReader

if t.TYPE_CHECKING:
    import pathlib

    from libtmux.server import Server


class FreezeTestFixture(t.NamedTuple):
    """Test fixture for tmuxp freeze command tests."""

    test_id: str
    cli_args: list[str]
    inputs: list[str]


class FreezeOverwriteTestFixture(t.NamedTuple):
    """Test fixture for tmuxp freeze overwrite command tests."""

    test_id: str
    cli_args: list[str]
    inputs: list[str]


FREEZE_TEST_FIXTURES: list[FreezeTestFixture] = [
    FreezeTestFixture(
        test_id="freeze_named_session",
        cli_args=["freeze", "myfrozensession"],
        inputs=["y\n", "./la.yaml\n", "y\n"],
    ),
    FreezeTestFixture(
        test_id="freeze_named_session_exists",
        cli_args=["freeze", "myfrozensession"],
        inputs=["y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
    ),
    FreezeTestFixture(
        test_id="freeze_current_session",
        cli_args=["freeze"],
        inputs=["y\n", "./la.yaml\n", "y\n"],
    ),
    FreezeTestFixture(
        test_id="freeze_current_session_exists",
        cli_args=["freeze"],
        inputs=["y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
    ),
]


FREEZE_OVERWRITE_TEST_FIXTURES: list[FreezeOverwriteTestFixture] = [
    FreezeOverwriteTestFixture(
        test_id="force_overwrite_named_session",
        cli_args=["freeze", "mysession", "--force"],
        inputs=["\n", "\n", "y\n", "./exists.yaml\n", "y\n"],
    ),
    FreezeOverwriteTestFixture(
        test_id="force_overwrite_current_session",
        cli_args=["freeze", "--force"],
        inputs=["\n", "\n", "y\n", "./exists.yaml\n", "y\n"],
    ),
]


@pytest.mark.parametrize(
    list(FreezeTestFixture._fields),
    FREEZE_TEST_FIXTURES,
    ids=[test.test_id for test in FREEZE_TEST_FIXTURES],
)
def test_freeze(
    server: Server,
    test_id: str,
    cli_args: list[str],
    inputs: list[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parametrized test for freezing a tmux session to a tmuxp config file."""
    monkeypatch.setenv("HOME", str(tmp_path))
    exists_yaml = tmp_path / "exists.yaml"
    exists_yaml.touch()

    server.new_session(session_name="myfirstsession")
    server.new_session(session_name="myfrozensession")

    # Assign an active pane to the session
    second_session = server.sessions[1]
    first_pane_on_second_session_id = second_session.windows[0].panes[0].pane_id
    assert first_pane_on_second_session_id
    monkeypatch.setenv("TMUX_PANE", first_pane_on_second_session_id)

    monkeypatch.chdir(tmp_path)
    # Use tmux server (socket name) used in the test
    assert server.socket_name is not None
    cli_args = [*cli_args, "-L", server.socket_name]

    monkeypatch.setattr("sys.stdin", io.StringIO("".join(inputs)))
    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    yaml_config_path = tmp_path / "la.yaml"
    assert yaml_config_path.exists()

    yaml_config = yaml_config_path.open().read()
    frozen_config = ConfigReader._load(fmt="yaml", content=yaml_config)

    assert frozen_config["session_name"] == "myfrozensession"


@pytest.mark.parametrize(
    list(FreezeOverwriteTestFixture._fields),
    FREEZE_OVERWRITE_TEST_FIXTURES,
    ids=[test.test_id for test in FREEZE_OVERWRITE_TEST_FIXTURES],
)
def test_freeze_overwrite(
    server: Server,
    test_id: str,
    cli_args: list[str],
    inputs: list[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test overwrite prompt when freezing a tmuxp configuration file."""
    monkeypatch.setenv("HOME", str(tmp_path))
    exists_yaml = tmp_path / "exists.yaml"
    exists_yaml.touch()

    server.new_session(session_name="mysession")

    monkeypatch.chdir(tmp_path)
    # Use tmux server (socket name) used in the test
    assert server.socket_name is not None
    cli_args = [*cli_args, "-L", server.socket_name]

    monkeypatch.setattr("sys.stdin", io.StringIO("".join(inputs)))
    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    yaml_config_path = tmp_path / "exists.yaml"
    assert yaml_config_path.exists()


def _freeze_help(dest: str) -> str:
    """Return the help text of the freeze flag storing into *dest*."""
    import argparse

    from tmuxp.cli.freeze import create_freeze_subparser

    parser = create_freeze_subparser(argparse.ArgumentParser(prog="freeze"))
    action = next(a for a in parser._actions if a.dest == dest)
    assert action.help is not None
    return action.help


def test_freeze_save_to_parses_as_a_path() -> None:
    """-o/--save-to stores a pathlib.Path, matching its declared type."""
    import argparse
    import pathlib

    from tmuxp.cli.freeze import create_freeze_subparser

    parser = create_freeze_subparser(argparse.ArgumentParser(prog="freeze"))
    args = parser.parse_args(["-o", "out.yaml"])
    assert isinstance(args.save_to, pathlib.Path)


def test_freeze_quiet_help_describes_what_it_silences() -> None:
    """--quiet advertises output suppression, not prompt suppression."""
    help_text = _freeze_help("quiet")
    assert "output" in help_text
    assert "--yes" in help_text


def test_freeze_force_help_scopes_itself_to_the_prompt() -> None:
    """--force advertises the prompted destination it actually affects."""
    assert "prompt" in _freeze_help("force")
