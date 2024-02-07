"""CLI tests for tmuxp's core shell functionality."""
import argparse
import contextlib
import pathlib
import typing as t

import libtmux
import pytest
from libtmux.server import Server

from tmuxp import cli
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.cli.import_config import get_teamocil_dir, get_tmuxinator_dir
from tmuxp.cli.load import _reattach, load_plugins
from tmuxp.cli.utils import tmuxp_echo
from tmuxp.workspace import loader
from tmuxp.workspace.builder import WorkspaceBuilder
from tmuxp.workspace.finders import find_workspace_file

from ..fixtures import utils as test_utils

if t.TYPE_CHECKING:
    import _pytest.capture


def test_creates_config_dir_not_exists(tmp_path: pathlib.Path) -> None:
    """cli.startup() creates config dir if not exists."""
    cli.startup(tmp_path)
    assert tmp_path.exists()


@pytest.mark.parametrize(
    "cli_args",
    [
        (["--help"]),
        (["-h"]),
    ],
)
def test_help(
    cli_args: t.List[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test tmuxp --help / -h."""
    # In scrunched terminals, prevent width causing differentiation in result.out.
    monkeypatch.setenv("COLUMNS", "100")
    monkeypatch.setenv("LINES", "100")

    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    result = capsys.readouterr()

    assert "usage: tmuxp [-h] [--version] [--log-level log-level]" in result.out


def test_resolve_behavior(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test resolution of file paths."""
    expect = tmp_path
    monkeypatch.chdir(tmp_path)
    assert pathlib.Path("../").resolve() == expect.parent
    assert pathlib.Path().resolve() == expect
    assert pathlib.Path("./").resolve() == expect
    assert pathlib.Path(expect).resolve() == expect


def test_get_tmuxinator_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_tmuxinator_dir() helper function."""
    assert get_tmuxinator_dir() == pathlib.Path("~/.tmuxinator").expanduser()

    monkeypatch.setenv("HOME", "/moo")
    assert get_tmuxinator_dir() == pathlib.Path("/moo/.tmuxinator/")
    assert str(get_tmuxinator_dir()) == "/moo/.tmuxinator"
    assert get_tmuxinator_dir() == pathlib.Path("~/.tmuxinator/").expanduser()


def test_get_teamocil_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_teamocil_dir() helper function."""
    assert get_teamocil_dir() == pathlib.Path("~/.teamocil/").expanduser()

    monkeypatch.setenv("HOME", "/moo")
    assert get_teamocil_dir() == pathlib.Path("/moo/.teamocil/")
    assert str(get_teamocil_dir()) == "/moo/.teamocil"
    assert get_teamocil_dir() == pathlib.Path("~/.teamocil/").expanduser()


def test_pass_config_dir_argparse(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test workspace configurations can be detected via directory."""
    configdir = tmp_path / "myconfigdir"
    configdir.mkdir()
    user_config_name = "myconfig"
    user_config = configdir / f"{user_config_name}.yaml"
    user_config.touch()

    expect = str(user_config)

    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_file", type=str)

    def config_cmd(workspace_file: str) -> None:
        tmuxp_echo(find_workspace_file(workspace_file, workspace_dir=configdir))

    def check_cmd(config_arg: str) -> "_pytest.capture.CaptureResult[str]":
        args = parser.parse_args([config_arg])
        config_cmd(workspace_file=args.workspace_file)
        return capsys.readouterr()

    monkeypatch.chdir(configdir)

    assert expect in check_cmd("myconfig").out
    assert expect in check_cmd("myconfig.yaml").out
    assert expect in check_cmd("./myconfig.yaml").out
    assert str(user_config) in check_cmd(str(configdir / "myconfig.yaml")).out

    with pytest.raises(FileNotFoundError):
        assert "FileNotFoundError" in check_cmd(".tmuxp.json").out


def test_reattach_plugins(
    monkeypatch_plugin_test_packages: None,
    server: "Server",
) -> None:
    """Test reattach plugin hook."""
    config_plugins = test_utils.read_workspace_file("workspace/builder/plugin_r.yaml")

    session_config = ConfigReader._load(fmt="yaml", content=config_plugins)
    session_config = loader.expand(session_config)

    # open it detached
    builder = WorkspaceBuilder(
        session_config=session_config,
        plugins=load_plugins(session_config),
        server=server,
    )
    builder.build()

    with contextlib.suppress(libtmux.exc.LibTmuxException):
        _reattach(builder)

    assert builder.session is not None
    proc = builder.session.cmd("display-message", "-p", "'#S'")

    assert proc.stdout[0] == "'plugin_test_r'"
