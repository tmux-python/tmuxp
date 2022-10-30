import argparse
import pathlib
import typing as t

import pytest

from tmuxp import cli
from tmuxp.cli.utils import tmuxp_echo
from tmuxp.workspace.finders import (
    find_workspace_file,
    get_workspace_dir,
    in_cwd,
    in_dir,
    is_pure_name,
)

if t.TYPE_CHECKING:
    import _pytest.capture


def test_in_dir_from_config_dir(tmp_path: pathlib.Path) -> None:
    """config.in_dir() finds configs config dir."""

    cli.startup(tmp_path)
    yaml_config = tmp_path / "myconfig.yaml"
    yaml_config.touch()
    json_config = tmp_path / "myconfig.json"
    json_config.touch()
    configs_found = in_dir(tmp_path)

    assert len(configs_found) == 2


def test_ignore_non_configs_from_current_dir(tmp_path: pathlib.Path) -> None:
    """cli.in_dir() ignore non-config from config dir."""

    cli.startup(tmp_path)

    junk_config = tmp_path / "myconfig.psd"
    junk_config.touch()
    conf = tmp_path / "watmyconfig.json"
    conf.touch()
    configs_found = in_dir(tmp_path)
    assert len(configs_found) == 1


def test_get_configs_cwd(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """config.in_cwd() find config in shell current working directory."""

    confdir = tmp_path / "tmuxpconf2"
    confdir.mkdir()

    monkeypatch.chdir(confdir)
    config1 = open(".tmuxp.json", "w+b")
    config1.close()

    configs_found = in_cwd()
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
def test_is_pure_name(path: str, expect: bool) -> None:
    assert is_pure_name(path) == expect


def test_tmuxp_configdir_env_var(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(tmp_path))

    assert get_workspace_dir() == str(tmp_path)


def test_tmuxp_configdir_xdg_config_dir(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    tmux_dir = tmp_path / "tmuxp"
    tmux_dir.mkdir()

    assert get_workspace_dir() == str(tmux_dir)


@pytest.fixture
def homedir(tmp_path: pathlib.Path) -> pathlib.Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


@pytest.fixture
def configdir(homedir: pathlib.Path) -> pathlib.Path:
    conf = homedir / ".tmuxp"
    conf.mkdir()
    return conf


@pytest.fixture
def projectdir(homedir: pathlib.Path) -> pathlib.Path:
    proj = homedir / "work" / "project"
    proj.mkdir(parents=True)
    return proj


def test_resolve_dot(
    tmp_path: pathlib.Path,
    homedir: pathlib.Path,
    configdir: pathlib.Path,
    projectdir: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    assert find_workspace_file(".") == expect
    assert find_workspace_file("./") == expect
    assert find_workspace_file("") == expect
    assert find_workspace_file("../project") == expect
    assert find_workspace_file("../project/") == expect
    assert find_workspace_file(".tmuxp.yaml") == expect
    assert find_workspace_file("../../.tmuxp/%s.yaml" % user_config_name) == str(
        user_config
    )
    assert find_workspace_file("myconfig") == str(user_config)
    assert find_workspace_file("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(Exception):
        find_workspace_file(".tmuxp.json")
    with pytest.raises(Exception):
        find_workspace_file(".tmuxp.ini")
    with pytest.raises(Exception):
        find_workspace_file("../")
    with pytest.raises(Exception):
        find_workspace_file("mooooooo")

    monkeypatch.chdir(homedir)

    expect = str(project_config)
    assert find_workspace_file("work/project") == expect
    assert find_workspace_file("work/project/") == expect
    assert find_workspace_file("./work/project") == expect
    assert find_workspace_file("./work/project/") == expect
    assert find_workspace_file(".tmuxp/%s.yaml" % user_config_name) == str(user_config)
    assert find_workspace_file("./.tmuxp/%s.yaml" % user_config_name) == str(
        user_config
    )
    assert find_workspace_file("myconfig") == str(user_config)
    assert find_workspace_file("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(Exception):
        find_workspace_file("")
    with pytest.raises(Exception):
        find_workspace_file(".")
    with pytest.raises(Exception):
        find_workspace_file(".tmuxp.yaml")
    with pytest.raises(Exception):
        find_workspace_file("../")
    with pytest.raises(Exception):
        find_workspace_file("mooooooo")

    monkeypatch.chdir(configdir)

    expect = str(project_config)
    assert find_workspace_file("../work/project") == expect
    assert find_workspace_file("../../home/work/project") == expect
    assert find_workspace_file("../work/project/") == expect
    assert find_workspace_file("%s.yaml" % user_config_name) == str(user_config)
    assert find_workspace_file("./%s.yaml" % user_config_name) == str(user_config)
    assert find_workspace_file("myconfig") == str(user_config)
    assert find_workspace_file("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(Exception):
        find_workspace_file("")
    with pytest.raises(Exception):
        find_workspace_file(".")
    with pytest.raises(Exception):
        find_workspace_file(".tmuxp.yaml")
    with pytest.raises(Exception):
        find_workspace_file("../")
    with pytest.raises(Exception):
        find_workspace_file("mooooooo")

    monkeypatch.chdir(tmp_path)

    expect = str(project_config)
    assert find_workspace_file("home/work/project") == expect
    assert find_workspace_file("./home/work/project/") == expect
    assert find_workspace_file("home/.tmuxp/%s.yaml" % user_config_name) == str(
        user_config
    )
    assert find_workspace_file("./home/.tmuxp/%s.yaml" % user_config_name) == str(
        user_config
    )
    assert find_workspace_file("myconfig") == str(user_config)
    assert find_workspace_file("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(Exception):
        find_workspace_file("")
    with pytest.raises(Exception):
        find_workspace_file(".")
    with pytest.raises(Exception):
        find_workspace_file(".tmuxp.yaml")
    with pytest.raises(Exception):
        find_workspace_file("../")
    with pytest.raises(Exception):
        find_workspace_file("mooooooo")


def test_find_workspace_file_arg(
    homedir: pathlib.Path,
    configdir: pathlib.Path,
    projectdir: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_file", type=str)

    def config_cmd(workspace_file: str) -> None:
        tmuxp_echo(find_workspace_file(workspace_file, workspace_dir=configdir))

    monkeypatch.setenv("HOME", str(homedir))
    tmuxp_config_path = projectdir / ".tmuxp.yaml"
    tmuxp_config_path.touch()
    user_config_name = "myconfig"
    user_config = configdir / f"{user_config_name}.yaml"
    user_config.touch()

    project_config = projectdir / ".tmuxp.yaml"

    def check_cmd(config_arg) -> "_pytest.capture.CaptureResult":
        args = parser.parse_args([config_arg])
        config_cmd(workspace_file=args.workspace_file)
        return capsys.readouterr()

    monkeypatch.chdir(projectdir)
    expect = str(project_config)
    assert expect in check_cmd(".").out
    assert expect in check_cmd("./").out
    assert expect in check_cmd("").out
    assert expect in check_cmd("../project").out
    assert expect in check_cmd("../project/").out
    assert expect in check_cmd(".tmuxp.yaml").out
    assert str(user_config) in check_cmd("../../.tmuxp/%s.yaml" % user_config_name).out
    assert user_config.stem in check_cmd("myconfig").out
    assert str(user_config) in check_cmd("~/.tmuxp/myconfig.yaml").out

    with pytest.raises(FileNotFoundError, match="file not found"):
        assert "file not found" in check_cmd(".tmuxp.json").err
    with pytest.raises(FileNotFoundError, match="file not found"):
        assert "file not found" in check_cmd(".tmuxp.ini").err
    with pytest.raises(FileNotFoundError, match="No tmuxp files found"):
        assert "No tmuxp files found" in check_cmd("../").err
    with pytest.raises(
        FileNotFoundError, match="workspace-file not found in workspace dir"
    ):
        assert "workspace-file not found in workspace dir" in check_cmd("moo").err
