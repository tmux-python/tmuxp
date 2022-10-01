"""Test for tmuxp command line interface."""
import json
import os
import pathlib
import typing as t

import pytest

import click
from click.testing import CliRunner
from pytest_mock import MockerFixture

import libtmux
from libtmux.common import has_lt_version
from libtmux.exc import LibTmuxException
from tmuxp import cli, config, exc
from tmuxp.cli.debug_info import command_debug_info
from tmuxp.cli.import_config import get_teamocil_dir, get_tmuxinator_dir
from tmuxp.cli.load import (
    _load_append_windows_to_current_session,
    _load_attached,
    _reattach,
    load_plugins,
    load_workspace,
)
from tmuxp.cli.ls import command_ls
from tmuxp.cli.utils import (
    ConfigPath,
    _validate_choices,
    get_abs_path,
    get_config_dir,
    is_pure_name,
    scan_config,
)
from tmuxp.config_reader import ConfigReader
from tmuxp.workspacebuilder import WorkspaceBuilder

from .constants import FIXTURE_PATH
from .fixtures import utils as test_utils

if t.TYPE_CHECKING:
    from libtmux.server import Server


def test_creates_config_dir_not_exists(tmp_path: pathlib.Path):
    """cli.startup() creates config dir if not exists."""

    cli.startup(tmp_path)
    assert os.path.exists(tmp_path)


def test_in_dir_from_config_dir(tmp_path: pathlib.Path):
    """config.in_dir() finds configs config dir."""

    cli.startup(tmp_path)
    yaml_config = tmp_path / "myconfig.yaml"
    yaml_config.touch()
    json_config = tmp_path / "myconfig.json"
    json_config.touch()
    configs_found = config.in_dir(tmp_path)

    assert len(configs_found) == 2


def test_ignore_non_configs_from_current_dir(tmp_path: pathlib.Path):
    """cli.in_dir() ignore non-config from config dir."""

    cli.startup(tmp_path)

    junk_config = tmp_path / "myconfig.psd"
    junk_config.touch()
    conf = tmp_path / "watmyconfig.json"
    conf.touch()
    configs_found = config.in_dir(tmp_path)
    assert len(configs_found) == 1


def test_get_configs_cwd(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    """config.in_cwd() find config in shell current working directory."""

    confdir = tmp_path / "tmuxpconf2"
    confdir.mkdir()

    monkeypatch.chdir(confdir)
    config1 = open(".tmuxp.json", "w+b")
    config1.close()

    configs_found = config.in_cwd()
    assert len(configs_found) == 1
    assert ".tmuxp.json" in configs_found


@pytest.mark.parametrize(
    "path,expect",
    [
        (".", False),
        ("./", False),
        ("", False),
        (".tmuxp.yaml", False),
        ("../.tmuxp.yaml", False),
        ("../", False),
        ("/hello/world", False),
        ("~/.tmuxp/hey", False),
        ("~/work/c/tmux/", False),
        ("~/work/c/tmux/.tmuxp.yaml", False),
        ("myproject", True),
    ],
)
def test_is_pure_name(path, expect):
    assert is_pure_name(path) == expect


"""
    scans for .tmuxp.{yaml,yml,json} in directory, returns first result
    log warning if multiple found:

    - current directory: ., ./, noarg
    - relative to cwd directory: ../, ./hello/, hello/, ./hello/
    - absolute directory: /path/to/dir, /path/to/dir/, ~/
    - no path, no ext, config_dir: projectname, tmuxp

    load file directly -

    - no directory (cwd): .tmuxp.yaml
    - relative to cwd: ../.tmuxp.yaml, ./hello/.tmuxp.yaml
    - absolute path: /path/to/file.yaml, ~/path/to/file/.tmuxp.yaml

    Any case where file is not found should return error.
"""


@pytest.fixture
def homedir(tmp_path: pathlib.Path):
    home = tmp_path / "home"
    home.mkdir()
    return home


@pytest.fixture
def configdir(homedir):
    conf = homedir / ".tmuxp"
    conf.mkdir()
    return conf


@pytest.fixture
def projectdir(homedir):
    proj = homedir / "work" / "project"
    proj.mkdir(parents=True)
    return proj


def test_tmuxp_configdir_env_var(tmp_path: pathlib.Path, monkeypatch):
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(tmp_path))

    assert get_config_dir() == str(tmp_path)


def test_tmuxp_configdir_xdg_config_dir(tmp_path: pathlib.Path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    tmux_dir = tmp_path / "tmuxp"
    tmux_dir.mkdir()

    assert get_config_dir() == str(tmux_dir)


def test_resolve_dot(
    tmp_path: pathlib.Path,
    homedir: pathlib.Path,
    configdir: pathlib.Path,
    projectdir: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("HOME", str(homedir))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(homedir / ".config"))

    tmuxp_conf_path = projectdir / ".tmuxp.yaml"
    tmuxp_conf_path.touch()
    user_config_name = "myconfig"
    user_config = configdir / f"{user_config_name}.yaml"
    user_config.touch()

    project_config = tmuxp_conf_path

    monkeypatch.chdir(projectdir)

    expect = str(project_config)
    assert scan_config(".") == expect
    assert scan_config("./") == expect
    assert scan_config("") == expect
    assert scan_config("../project") == expect
    assert scan_config("../project/") == expect
    assert scan_config(".tmuxp.yaml") == expect
    assert scan_config("../../.tmuxp/%s.yaml" % user_config_name) == str(user_config)
    assert scan_config("myconfig") == str(user_config)
    assert scan_config("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(Exception):
        scan_config(".tmuxp.json")
    with pytest.raises(Exception):
        scan_config(".tmuxp.ini")
    with pytest.raises(Exception):
        scan_config("../")
    with pytest.raises(Exception):
        scan_config("mooooooo")

    monkeypatch.chdir(homedir)

    expect = str(project_config)
    assert scan_config("work/project") == expect
    assert scan_config("work/project/") == expect
    assert scan_config("./work/project") == expect
    assert scan_config("./work/project/") == expect
    assert scan_config(".tmuxp/%s.yaml" % user_config_name) == str(user_config)
    assert scan_config("./.tmuxp/%s.yaml" % user_config_name) == str(user_config)
    assert scan_config("myconfig") == str(user_config)
    assert scan_config("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(Exception):
        scan_config("")
    with pytest.raises(Exception):
        scan_config(".")
    with pytest.raises(Exception):
        scan_config(".tmuxp.yaml")
    with pytest.raises(Exception):
        scan_config("../")
    with pytest.raises(Exception):
        scan_config("mooooooo")

    monkeypatch.chdir(configdir)

    expect = str(project_config)
    assert scan_config("../work/project") == expect
    assert scan_config("../../home/work/project") == expect
    assert scan_config("../work/project/") == expect
    assert scan_config("%s.yaml" % user_config_name) == str(user_config)
    assert scan_config("./%s.yaml" % user_config_name) == str(user_config)
    assert scan_config("myconfig") == str(user_config)
    assert scan_config("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(Exception):
        scan_config("")
    with pytest.raises(Exception):
        scan_config(".")
    with pytest.raises(Exception):
        scan_config(".tmuxp.yaml")
    with pytest.raises(Exception):
        scan_config("../")
    with pytest.raises(Exception):
        scan_config("mooooooo")

    monkeypatch.chdir(tmp_path)

    expect = str(project_config)
    assert scan_config("home/work/project") == expect
    assert scan_config("./home/work/project/") == expect
    assert scan_config("home/.tmuxp/%s.yaml" % user_config_name) == str(user_config)
    assert scan_config("./home/.tmuxp/%s.yaml" % user_config_name) == str(user_config)
    assert scan_config("myconfig") == str(user_config)
    assert scan_config("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(Exception):
        scan_config("")
    with pytest.raises(Exception):
        scan_config(".")
    with pytest.raises(Exception):
        scan_config(".tmuxp.yaml")
    with pytest.raises(Exception):
        scan_config("../")
    with pytest.raises(Exception):
        scan_config("mooooooo")


def test_scan_config_arg(
    homedir, configdir, projectdir, monkeypatch: pytest.MonkeyPatch
):
    runner = CliRunner()

    @click.command()
    @click.argument("config", type=ConfigPath(exists=True), nargs=-1)
    def config_cmd(config):
        click.echo(config)

    monkeypatch.setenv("HOME", str(homedir))
    tmuxp_config_path = projectdir / ".tmuxp.yaml"
    tmuxp_config_path.touch()
    user_config_name = "myconfig"
    user_config = configdir / f"{user_config_name}.yaml"
    user_config.touch()

    project_config = projectdir / ".tmuxp.yaml"

    def check_cmd(config_arg):
        return runner.invoke(config_cmd, [config_arg]).output

    monkeypatch.chdir(projectdir)
    expect = str(project_config)
    assert expect in check_cmd(".")
    assert expect in check_cmd("./")
    assert expect in check_cmd("")
    assert expect in check_cmd("../project")
    assert expect in check_cmd("../project/")
    assert expect in check_cmd(".tmuxp.yaml")
    assert str(user_config) in check_cmd("../../.tmuxp/%s.yaml" % user_config_name)
    assert user_config.stem in check_cmd("myconfig")
    assert str(user_config) in check_cmd("~/.tmuxp/myconfig.yaml")

    assert "file not found" in check_cmd(".tmuxp.json")
    assert "file not found" in check_cmd(".tmuxp.ini")
    assert "No tmuxp files found" in check_cmd("../")
    assert "config not found in config dir" in check_cmd("moo")


def test_load_workspace(server, monkeypatch):
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspacebuilder" / "two_pane.yaml"

    # open it detached
    session = load_workspace(
        session_file, socket_name=server.socket_name, detached=True
    )

    assert isinstance(session, libtmux.Session)
    assert session.name == "sampleconfig"


def test_load_workspace_named_session(server, monkeypatch):
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspacebuilder" / "two_pane.yaml"

    # open it detached
    session = load_workspace(
        session_file,
        socket_name=server.socket_name,
        new_session_name="tmuxp-new",
        detached=True,
    )

    assert isinstance(session, libtmux.Session)
    assert session.name == "tmuxp-new"


@pytest.mark.skipif(
    has_lt_version("2.1"), reason="exact session name matches only tmux >= 2.1"
)
def test_load_workspace_name_match_regression_252(
    tmp_path: pathlib.Path, server, monkeypatch
):
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspacebuilder" / "two_pane.yaml"

    # open it detached
    session = load_workspace(
        session_file, socket_name=server.socket_name, detached=True
    )

    assert isinstance(session, libtmux.Session)
    assert session.name == "sampleconfig"

    projfile = tmp_path / "simple.yaml"

    projfile.write_text(
        """
session_name: sampleconfi
start_directory: './'
windows:
- panes:
    - echo 'hey'""",
        encoding="utf-8",
    )

    # open it detached
    session = load_workspace(
        str(projfile), socket_name=server.socket_name, detached=True
    )
    assert session.name == "sampleconfi"


def test_load_symlinked_workspace(server, tmp_path, monkeypatch):
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv("TMUX", raising=False)

    realtemp = tmp_path / "myrealtemp"
    realtemp.mkdir()
    linktemp = tmp_path / "symlinktemp"
    linktemp.symlink_to(realtemp)
    projfile = linktemp / "simple.yaml"

    projfile.write_text(
        """
session_name: samplesimple
start_directory: './'
windows:
- panes:
    - echo 'hey'""",
        encoding="utf-8",
    )

    # open it detached
    session = load_workspace(
        str(projfile), socket_name=server.socket_name, detached=True
    )
    pane = session.attached_window.attached_pane

    assert isinstance(session, libtmux.Session)
    assert session.name == "samplesimple"
    assert pane.current_path == str(realtemp)


def test_regression_00132_session_name_with_dots(
    tmp_path: pathlib.Path, server, session
):
    yaml_config = FIXTURE_PATH / "workspacebuilder" / "regression_00132_dots.yaml"
    cli_args = [str(yaml_config)]
    inputs: t.List[str] = []
    runner = CliRunner()
    result = runner.invoke(
        cli.command_load, cli_args, input="".join(inputs), standalone_mode=False
    )
    assert result.exception
    assert isinstance(result.exception, libtmux.exc.BadSessionName)


@pytest.mark.parametrize("cli_args", [(["load", "."]), (["load", ".tmuxp.yaml"])])
def test_load_zsh_autotitle_warning(cli_args, tmp_path, monkeypatch):
    # create dummy tmuxp yaml so we don't get yelled at
    yaml_config = tmp_path / ".tmuxp.yaml"
    yaml_config.touch()
    oh_my_zsh_path = tmp_path / ".oh-my-zsh"
    oh_my_zsh_path.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    monkeypatch.delenv("DISABLE_AUTO_TITLE", raising=False)
    monkeypatch.setenv("SHELL", "zsh")
    result = runner.invoke(cli.cli, cli_args)
    assert "Please set" in result.output

    monkeypatch.setenv("DISABLE_AUTO_TITLE", "false")
    result = runner.invoke(cli.cli, cli_args)
    assert "Please set" in result.output

    monkeypatch.setenv("DISABLE_AUTO_TITLE", "true")
    result = runner.invoke(cli.cli, cli_args)
    assert "Please set" not in result.output

    monkeypatch.delenv("DISABLE_AUTO_TITLE", raising=False)
    monkeypatch.setenv("SHELL", "sh")
    result = runner.invoke(cli.cli, cli_args)
    assert "Please set" not in result.output


@pytest.mark.parametrize(
    "cli_args",
    [
        (["load", ".", "--log-file", "log.txt"]),
    ],
)
def test_load_log_file(cli_args, tmp_path, monkeypatch):
    # create dummy tmuxp yaml that breaks to prevent actually loading tmux
    tmuxp_config_path = tmp_path / ".tmuxp.yaml"
    tmuxp_config_path.write_text(
        """
session_name: hello
        """,
        encoding="utf-8",
    )
    oh_my_zsh_path = tmp_path / ".oh-my-zsh"
    oh_my_zsh_path.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    # If autoconfirm (-y) no need to prompt y
    input_args = "y\ny\n" if "-y" not in cli_args else ""

    result = runner.invoke(cli.cli, cli_args, input=input_args)
    log_file_path = tmp_path / "log.txt"
    assert "Loading" in log_file_path.open().read()
    assert result is not None


@pytest.mark.parametrize("cli_cmd", ["shell", ("shell", "--pdb")])
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
    cli_cmd,
    cli_args,
    inputs,
    expected_output,
    env,
    tmp_path,
    monkeypatch,
    server,
    session,
):
    monkeypatch.setenv("HOME", str(tmp_path))
    window_name = "my_window"
    window = session.new_window(window_name=window_name)
    window.split_window()

    template_ctx = dict(
        SOCKET_NAME=server.socket_name,
        SOCKET_PATH=server.socket_path,
        SESSION_NAME=session.name,
        WINDOW_NAME=window_name,
        PANE_ID=window.attached_pane.id,
        SERVER_SOCKET_NAME=server.socket_name,
    )

    cli_cmd = list(cli_cmd) if isinstance(cli_cmd, (list, tuple)) else [cli_cmd]
    cli_args = cli_cmd + [cli_arg.format(**template_ctx) for cli_arg in cli_args]

    for k, v in env.items():
        monkeypatch.setenv(k, v.format(**template_ctx))

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli.cli, cli_args, input="".join(inputs), catch_exceptions=False
    )
    assert expected_output.format(**template_ctx) in result.output


@pytest.mark.parametrize(
    "cli_cmd",
    [
        "shell",
        ("shell", "--pdb"),
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
            LibTmuxException,
            r".*DoesNotExist.*",
        ),
        (
            [
                "-L{SOCKET_NAME}",
                "nonexistant_session",
                "-c",
                "print(str(server.socket_name))",
            ],
            [],
            {},
            {"session_name": "nonexistant_session"},
            exc.TmuxpException,
            "Session not found: nonexistant_session",
        ),
        (
            [
                "-L{SOCKET_NAME}",
                "{SESSION_NAME}",
                "nonexistant_window",
                "-c",
                "print(str(server.socket_name))",
            ],
            [],
            {},
            {"window_name": "nonexistant_window"},
            exc.TmuxpException,
            "Window not found: {WINDOW_NAME}",
        ),
    ],
)
def test_shell_target_missing(
    cli_cmd,
    cli_args,
    inputs,
    env,
    template_ctx,
    exception,
    message,
    tmp_path,
    monkeypatch,
    socket_name,
    server,
    session,
):
    monkeypatch.setenv("HOME", str(tmp_path))
    window_name = "my_window"
    window = session.new_window(window_name=window_name)
    window.split_window()

    template_ctx = dict(
        SOCKET_NAME=server.socket_name,
        SOCKET_PATH=server.socket_path,
        SESSION_NAME=session.name,
        WINDOW_NAME=template_ctx.get("window_name", window_name),
        PANE_ID=template_ctx.get("pane_id"),
        SERVER_SOCKET_NAME=server.socket_name,
    )
    cli_cmd = list(cli_cmd) if isinstance(cli_cmd, (list, tuple)) else [cli_cmd]
    cli_args = cli_cmd + [cli_arg.format(**template_ctx) for cli_arg in cli_args]

    for k, v in env.items():
        monkeypatch.setenv(k, v.format(**template_ctx))

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    if exception is not None:
        with pytest.raises(exception, match=message.format(**template_ctx)):
            result = runner.invoke(
                cli.cli, cli_args, input="".join(inputs), catch_exceptions=False
            )
    else:
        result = runner.invoke(
            cli.cli, cli_args, input="".join(inputs), catch_exceptions=False
        )
        assert message.format(**template_ctx) in result.output


@pytest.mark.parametrize(
    "cli_cmd",
    [
        # 'shell',
        # ('shell', '--pdb'),
        ("shell", "--code"),
        # ('shell', '--bpython'),
        # ('shell', '--ptipython'),
        # ('shell', '--ptpython'),
        # ('shell', '--ipython'),
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
def test_shell_plus(
    cli_cmd,
    cli_args,
    inputs,
    env,
    message,
    tmp_path,
    monkeypatch,
    server,
    session,
):
    monkeypatch.setenv("HOME", str(tmp_path))
    window_name = "my_window"
    window = session.new_window(window_name=window_name)
    window.split_window()

    template_ctx = dict(
        SOCKET_NAME=server.socket_name,
        SOCKET_PATH=server.socket_path,
        SESSION_NAME=session.name,
        WINDOW_NAME=window_name,
        PANE_ID=window.attached_pane.id,
        SERVER_SOCKET_NAME=server.socket_name,
    )

    cli_cmd = list(cli_cmd) if isinstance(cli_cmd, (list, tuple)) else [cli_cmd]
    cli_args = cli_cmd + [cli_arg.format(**template_ctx) for cli_arg in cli_args]

    for k, v in env.items():
        monkeypatch.setenv(k, v.format(**template_ctx))

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli.cli, cli_args, input="".join(inputs), catch_exceptions=True
    )
    assert message.format(**template_ctx) in result.output


@pytest.mark.parametrize(
    "cli_args",
    [
        (["convert", "."]),
        (["convert", ".tmuxp.yaml"]),
        (["convert", ".tmuxp.yaml", "-y"]),
        (["convert", ".tmuxp.yml"]),
        (["convert", ".tmuxp.yml", "-y"]),
    ],
)
def test_convert(cli_args, tmp_path, monkeypatch):
    # create dummy tmuxp yaml so we don't get yelled at
    filename = cli_args[1]
    if filename == ".":
        filename = ".tmuxp.yaml"
    file_ext = filename.rsplit(".", 1)[-1]
    assert file_ext in ["yaml", "yml"], file_ext
    config_file_path = tmp_path / filename
    config_file_path.write_text("\nsession_name: hello\n", encoding="utf-8")
    oh_my_zsh_path = tmp_path / ".oh-my-zsh"
    oh_my_zsh_path.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    # If autoconfirm (-y) no need to prompt y
    input_args = "y\ny\n" if "-y" not in cli_args else ""

    runner.invoke(cli.cli, cli_args, input=input_args)
    tmuxp_json = tmp_path / ".tmuxp.json"
    assert tmuxp_json.exists()
    assert tmuxp_json.open().read() == json.dumps({"session_name": "hello"}, indent=2)


@pytest.mark.parametrize(
    "cli_args",
    [
        (["convert", "."]),
        (["convert", ".tmuxp.json"]),
        (["convert", ".tmuxp.json", "-y"]),
    ],
)
def test_convert_json(cli_args, tmp_path, monkeypatch):
    # create dummy tmuxp yaml so we don't get yelled at
    json_config = tmp_path / ".tmuxp.json"
    json_config.write_text('{"session_name": "hello"}', encoding="utf-8")
    oh_my_zsh_path = tmp_path / ".oh-my-zsh"
    oh_my_zsh_path.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    # If autoconfirm (-y) no need to prompt y
    input_args = "y\ny\n" if "-y" not in cli_args else ""

    runner.invoke(cli.cli, cli_args, input=input_args)
    tmuxp_yaml = tmp_path / ".tmuxp.yaml"
    assert tmuxp_yaml.exists()
    assert tmuxp_yaml.open().read() == "session_name: hello\n"


@pytest.mark.parametrize("cli_args", [(["import"])])
def test_import(cli_args, monkeypatch):
    runner = CliRunner()

    result = runner.invoke(cli.cli, cli_args)
    assert "tmuxinator" in result.output
    assert "teamocil" in result.output


@pytest.mark.parametrize(
    "cli_args",
    [
        (["--help"]),
        (["-h"]),
    ],
)
def test_help(cli_args, monkeypatch):
    runner = CliRunner()

    result = runner.invoke(cli.cli, cli_args)
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in result.output


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (
            ["import", "teamocil", "./.teamocil/config.yaml"],
            ["\n", "y\n", "./la.yaml\n", "y\n"],
        ),
        (
            ["import", "teamocil", "./.teamocil/config.yaml"],
            ["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
        ),
        (
            ["import", "teamocil", "config"],
            ["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
        ),
    ],
)
def test_import_teamocil(cli_args, inputs, tmp_path, monkeypatch):
    teamocil_config = test_utils.read_config_file("config_teamocil/test4.yaml")

    teamocil_path = tmp_path / ".teamocil"
    teamocil_path.mkdir()

    teamocil_config_path = teamocil_path / "config.yaml"
    teamocil_config_path.write_text(teamocil_config, encoding="utf-8")

    exists_yaml = tmp_path / "exists.yaml"
    exists_yaml.touch()

    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli.cli, cli_args, input="".join(inputs))

    new_config_yaml = tmp_path / "la.yaml"
    assert new_config_yaml.exists()


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (
            ["import", "tmuxinator", "./.tmuxinator/config.yaml"],
            ["\n", "y\n", "./la.yaml\n", "y\n"],
        ),
        (
            ["import", "tmuxinator", "./.tmuxinator/config.yaml"],
            ["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
        ),
        (
            ["import", "tmuxinator", "config"],
            ["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
        ),
    ],
)
def test_import_tmuxinator(cli_args, inputs, tmp_path, monkeypatch):
    tmuxinator_config = test_utils.read_config_file("config_tmuxinator/test3.yaml")

    tmuxinator_path = tmp_path / ".tmuxinator"
    tmuxinator_path.mkdir()

    tmuxinator_config_path = tmuxinator_path / "config.yaml"
    tmuxinator_config_path.write_text(tmuxinator_config, encoding="utf-8")

    exists_yaml = tmp_path / "exists.yaml"
    exists_yaml.touch()

    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    out = runner.invoke(cli.cli, cli_args, input="".join(inputs))
    print(out.output)
    new_config_yaml = tmp_path / "la.yaml"
    assert new_config_yaml.exists()


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (["freeze", "myfrozensession"], ["y\n", "./la.yaml\n", "y\n"]),
        (  # Exists
            ["freeze", "myfrozensession"],
            ["y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
        ),
        (  # Imply current session if not entered
            ["freeze"],
            ["y\n", "./la.yaml\n", "y\n"],
        ),
        (["freeze"], ["y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"]),  # Exists
    ],
)
def test_freeze(server, cli_args, inputs, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    exists_yaml = tmp_path / "exists.yaml"
    exists_yaml.touch()

    server.new_session(session_name="myfirstsession")
    server.new_session(session_name="myfrozensession")

    # Assign an active pane to the session
    second_session = server.list_sessions()[1]
    first_pane_on_second_session_id = second_session.list_windows()[0].list_panes()[0][
        "pane_id"
    ]
    monkeypatch.setenv("TMUX_PANE", first_pane_on_second_session_id)

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    # Use tmux server (socket name) used in the test
    cli_args = cli_args + ["-L", server.socket_name]
    out = runner.invoke(cli.cli, cli_args, input="".join(inputs))
    print(out.output)

    yaml_config_path = tmp_path / "la.yaml"
    assert yaml_config_path.exists()

    yaml_config = yaml_config_path.open().read()
    frozen_config = ConfigReader._load(format="yaml", content=yaml_config)

    assert frozen_config["session_name"] == "myfrozensession"


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (  # Overwrite
            ["freeze", "mysession", "--force"],
            ["\n", "y\n", "./exists.yaml\n", "y\n"],
        ),
        (  # Imply current session if not entered
            ["freeze", "--force"],
            ["\n", "y\n", "./exists.yaml\n", "y\n"],
        ),
    ],
)
def test_freeze_overwrite(server, cli_args, inputs, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    exists_yaml = tmp_path / "exists.yaml"
    exists_yaml.touch()

    server.new_session(session_name="mysession")

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    # Use tmux server (socket name) used in the test
    cli_args = cli_args + ["-L", server.socket_name]
    out = runner.invoke(cli.cli, cli_args, input="".join(inputs))
    print(out.output)

    yaml_config_path = tmp_path / "exists.yaml"
    assert yaml_config_path.exists()


def test_get_abs_path(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    expect = str(tmp_path)
    monkeypatch.chdir(tmp_path)
    get_abs_path("../") == os.path.dirname(expect)
    get_abs_path(".") == expect
    get_abs_path("./") == expect
    get_abs_path(expect) == expect


def test_get_tmuxinator_dir(monkeypatch):
    assert get_tmuxinator_dir() == os.path.expanduser("~/.tmuxinator/")

    monkeypatch.setenv("HOME", "/moo")
    assert get_tmuxinator_dir() == "/moo/.tmuxinator/"
    assert get_tmuxinator_dir() == os.path.expanduser("~/.tmuxinator/")


def test_get_teamocil_dir(monkeypatch: pytest.MonkeyPatch):
    assert get_teamocil_dir() == os.path.expanduser("~/.teamocil/")

    monkeypatch.setenv("HOME", "/moo")
    assert get_teamocil_dir() == "/moo/.teamocil/"
    assert get_teamocil_dir() == os.path.expanduser("~/.teamocil/")


def test_validate_choices():
    validate = _validate_choices(["choice1", "choice2"])

    assert validate("choice1")
    assert validate("choice2")

    with pytest.raises(click.BadParameter):
        assert validate("choice3")


def test_pass_config_dir_ClickPath(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):

    configdir = tmp_path / "myconfigdir"
    configdir.mkdir()
    user_config_name = "myconfig"
    user_config = configdir / f"{user_config_name}.yaml"
    user_config.touch()

    expect = str(user_config)

    runner = CliRunner()

    @click.command()
    @click.argument(
        "config",
        type=ConfigPath(exists=True, config_dir=(str(configdir))),
        nargs=-1,
    )
    def config_cmd(config):
        click.echo(config)

    def check_cmd(config_arg):
        return runner.invoke(config_cmd, [config_arg]).output

    monkeypatch.chdir(configdir)

    assert expect in check_cmd("myconfig")
    assert expect in check_cmd("myconfig.yaml")
    assert expect in check_cmd("./myconfig.yaml")
    assert str(user_config) in check_cmd(str(configdir / "myconfig.yaml"))

    assert "file not found" in check_cmd(".tmuxp.json")


def test_ls_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))

    filenames = [
        ".git/",
        ".gitignore/",
        "session_1.yaml",
        "session_2.yaml",
        "session_3.json",
        "session_4.txt",
    ]

    # should ignore:
    # - directories should be ignored
    # - extensions not covered in VALID_CONFIG_DIR_FILE_EXTENSIONS
    ignored_filenames = [".git/", ".gitignore/", "session_4.txt"]
    stems = [os.path.splitext(f)[0] for f in filenames if f not in ignored_filenames]

    for filename in filenames:
        location = tmp_path / f".tmuxp/{filename}"
        if filename.endswith("/"):
            location.mkdir(parents=True)
        else:
            location.touch()

    runner = CliRunner()
    cli_output = runner.invoke(command_ls).output
    assert cli_output == "\n".join(stems) + "\n"


def test_load_plugins(monkeypatch_plugin_test_packages):
    from tmuxp_test_plugin_bwb.plugin import PluginBeforeWorkspaceBuilder

    plugins_config = test_utils.read_config_file("workspacebuilder/plugin_bwb.yaml")

    sconfig = ConfigReader._load(format="yaml", content=plugins_config)
    sconfig = config.expand(sconfig)

    plugins = load_plugins(sconfig)

    assert len(plugins) == 1

    test_plugin_class_types = [
        PluginBeforeWorkspaceBuilder().__class__,
    ]
    for plugin in plugins:
        assert plugin.__class__ in test_plugin_class_types


@pytest.mark.skip("Not sure how to clean up the tmux session this makes")
@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (
            ["load", "tests/fixtures/workspacebuilder/plugin_versions_fail.yaml"],
            ["y\n"],
        )
    ],
)
def test_load_plugins_version_fail_skip(
    monkeypatch_plugin_test_packages, cli_args, inputs
):
    runner = CliRunner()

    results = runner.invoke(cli.cli, cli_args, input="".join(inputs))
    assert "[Loading]" in results.output


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (
            ["load", "tests/fixtures/workspacebuilder/plugin_versions_fail.yaml"],
            ["n\n"],
        )
    ],
)
def test_load_plugins_version_fail_no_skip(
    monkeypatch_plugin_test_packages, cli_args, inputs
):
    runner = CliRunner()

    results = runner.invoke(cli.cli, cli_args, input="".join(inputs))
    assert "[Not Skipping]" in results.output


@pytest.mark.parametrize(
    "cli_args", [(["load", "tests/fixtures/workspacebuilder/plugin_missing_fail.yaml"])]
)
def test_load_plugins_plugin_missing(monkeypatch_plugin_test_packages, cli_args):
    runner = CliRunner()

    results = runner.invoke(cli.cli, cli_args)
    assert "[Plugin Error]" in results.output


def test_plugin_system_before_script(
    monkeypatch_plugin_test_packages, server, monkeypatch
):
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspacebuilder" / "plugin_bs.yaml"

    # open it detached
    session = load_workspace(
        session_file, socket_name=server.socket_name, detached=True
    )

    assert isinstance(session, libtmux.Session)
    assert session.name == "plugin_test_bs"


def test_reattach_plugins(monkeypatch_plugin_test_packages, server):
    config_plugins = test_utils.read_config_file("workspacebuilder/plugin_r.yaml")

    sconfig = ConfigReader._load(format="yaml", content=config_plugins)
    sconfig = config.expand(sconfig)

    # open it detached
    builder = WorkspaceBuilder(
        sconf=sconfig, plugins=load_plugins(sconfig), server=server
    )
    builder.build()

    try:
        _reattach(builder)
    except libtmux.exc.LibTmuxException:
        pass

    proc = builder.session.cmd("display-message", "-p", "'#S'")

    assert proc.stdout[0] == "'plugin_test_r'"


def test_load_attached(
    server: "Server", monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    # Load a session and attach from outside tmux
    monkeypatch.delenv("TMUX", raising=False)

    attach_session_mock = mocker.patch("libtmux.session.Session.attach_session")
    attach_session_mock.return_value.stderr = None

    yaml_config = test_utils.read_config_file("workspacebuilder/two_pane.yaml")
    sconfig = ConfigReader._load(format="yaml", content=yaml_config)

    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    _load_attached(builder, False)

    assert attach_session_mock.call_count == 1


def test_load_attached_detached(
    server: "Server", monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    # Load a session but don't attach
    monkeypatch.delenv("TMUX", raising=False)

    attach_session_mock = mocker.patch("libtmux.session.Session.attach_session")
    attach_session_mock.return_value.stderr = None

    yaml_config = test_utils.read_config_file("workspacebuilder/two_pane.yaml")
    sconfig = ConfigReader._load(format="yaml", content=yaml_config)

    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    _load_attached(builder, True)

    assert attach_session_mock.call_count == 0


def test_load_attached_within_tmux(
    server: "Server", monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    # Load a session and attach from within tmux
    monkeypatch.setenv("TMUX", "/tmp/tmux-1234/default,123,0")

    switch_client_mock = mocker.patch("libtmux.session.Session.switch_client")
    switch_client_mock.return_value.stderr = None

    yaml_config = test_utils.read_config_file("workspacebuilder/two_pane.yaml")
    sconfig = ConfigReader._load(format="yaml", content=yaml_config)

    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    _load_attached(builder, False)

    assert switch_client_mock.call_count == 1


def test_load_attached_within_tmux_detached(
    server: "Server", monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    # Load a session and attach from within tmux
    monkeypatch.setenv("TMUX", "/tmp/tmux-1234/default,123,0")

    switch_client_mock = mocker.patch("libtmux.session.Session.switch_client")
    switch_client_mock.return_value.stderr = None

    yaml_config = test_utils.read_config_file("workspacebuilder/two_pane.yaml")
    sconfig = ConfigReader._load(format="yaml", content=yaml_config)

    builder = WorkspaceBuilder(sconf=sconfig, server=server)

    _load_attached(builder, True)

    assert switch_client_mock.call_count == 1


def test_load_append_windows_to_current_session(server, monkeypatch):
    yaml_config = test_utils.read_config_file("workspacebuilder/two_pane.yaml")
    sconfig = ConfigReader._load(format="yaml", content=yaml_config)

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    builder.build()

    assert len(server.list_sessions()) == 1
    assert len(server._list_windows()) == 3

    # Assign an active pane to the session
    monkeypatch.setenv("TMUX_PANE", server._list_panes()[0]["pane_id"])

    builder = WorkspaceBuilder(sconf=sconfig, server=server)
    _load_append_windows_to_current_session(builder)

    assert len(server.list_sessions()) == 1
    assert len(server._list_windows()) == 6


def test_debug_info_cli(monkeypatch, tmp_path: pathlib.Path):
    monkeypatch.setenv("SHELL", "/bin/bash")

    runner = CliRunner()
    cli_output = runner.invoke(command_debug_info).output
    assert "environment" in cli_output
    assert "python version" in cli_output
    assert "system PATH" in cli_output
    assert "tmux version" in cli_output
    assert "libtmux version" in cli_output
    assert "tmuxp version" in cli_output
    assert "tmux path" in cli_output
    assert "tmuxp path" in cli_output
    assert "shell" in cli_output
    assert "tmux session" in cli_output
    assert "tmux windows" in cli_output
    assert "tmux panes" in cli_output
    assert "tmux global options" in cli_output
    assert "tmux window options" in cli_output
