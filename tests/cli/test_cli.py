import argparse
import os
import pathlib
import typing as t

import pytest

import libtmux
from libtmux.server import Server
from tmuxp import cli
from tmuxp.cli.import_config import get_teamocil_dir, get_tmuxinator_dir
from tmuxp.cli.load import _reattach, load_plugins
from tmuxp.cli.utils import tmuxp_echo
from tmuxp.config_reader import ConfigReader
from tmuxp.workspace import loader
from tmuxp.workspace.builder import WorkspaceBuilder
from tmuxp.workspace.finders import find_workspace_file

from ..fixtures import utils as test_utils

if t.TYPE_CHECKING:
    import _pytest.capture


def test_creates_config_dir_not_exists(tmp_path: pathlib.Path) -> None:
    """cli.startup() creates config dir if not exists."""

    cli.startup(tmp_path)
    assert os.path.exists(tmp_path)


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
    capsys: pytest.CaptureFixture,
) -> None:
    try:
        cli.cli(cli_args)
    except SystemExit:
        pass
    result = capsys.readouterr()

    assert "usage: tmuxp [-h] [--version] [--log-level log-level]" in result.out


def test_resolve_behavior(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expect = tmp_path
    monkeypatch.chdir(tmp_path)
    assert pathlib.Path("../").resolve() == pathlib.Path(os.path.dirname(expect))
    assert pathlib.Path(".").resolve() == expect
    assert pathlib.Path("./").resolve() == expect
    assert pathlib.Path(expect).resolve() == expect


def test_get_tmuxinator_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    assert get_tmuxinator_dir() == os.path.expanduser("~/.tmuxinator/")

    monkeypatch.setenv("HOME", "/moo")
    assert get_tmuxinator_dir() == "/moo/.tmuxinator/"
    assert get_tmuxinator_dir() == os.path.expanduser("~/.tmuxinator/")


def test_get_teamocil_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    assert get_teamocil_dir() == os.path.expanduser("~/.teamocil/")

    monkeypatch.setenv("HOME", "/moo")
    assert get_teamocil_dir() == "/moo/.teamocil/"
    assert get_teamocil_dir() == os.path.expanduser("~/.teamocil/")


def test_pass_config_dir_ClickPath(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:

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

    def check_cmd(config_arg) -> "_pytest.capture.CaptureResult":
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
    monkeypatch_plugin_test_packages: None, server: "Server"
) -> None:
    config_plugins = test_utils.read_workspace_file("workspace/builder/plugin_r.yaml")

    session_configig = ConfigReader._load(format="yaml", content=config_plugins)
    session_configig = loader.expand(session_configig)

    # open it detached
    builder = WorkspaceBuilder(
        session_config=session_configig,
        plugins=load_plugins(session_configig),
        server=server,
    )
    builder.build()

    try:
        _reattach(builder)
    except libtmux.exc.LibTmuxException:
        pass

    assert builder.session is not None
    proc = builder.session.cmd("display-message", "-p", "'#S'")

    assert proc.stdout[0] == "'plugin_test_r'"
