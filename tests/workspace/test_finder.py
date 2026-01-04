"""Test config file searching for tmuxp."""

from __future__ import annotations

import argparse
import pathlib
import typing as t

import pytest

from tmuxp import cli
from tmuxp.cli.utils import tmuxp_echo
from tmuxp.workspace.finders import (
    find_workspace_file,
    get_workspace_dir,
    get_workspace_dir_candidates,
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
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """config.in_cwd() find config in shell current working directory."""
    confdir = tmp_path / "tmuxpconf2"
    confdir.mkdir()

    monkeypatch.chdir(confdir)
    with pathlib.Path(".tmuxp.json").open("w+b") as config1:
        config1.close()

    configs_found = in_cwd()
    assert len(configs_found) == 1
    assert ".tmuxp.json" in configs_found


class PureNameTestFixture(t.NamedTuple):
    """Test fixture for verifying pure name path validation."""

    test_id: str
    path: str
    expect: bool


PURE_NAME_TEST_FIXTURES: list[PureNameTestFixture] = [
    PureNameTestFixture(
        test_id="current_dir",
        path=".",
        expect=False,
    ),
    PureNameTestFixture(
        test_id="current_dir_slash",
        path="./",
        expect=False,
    ),
    PureNameTestFixture(
        test_id="empty_path",
        path="",
        expect=False,
    ),
    PureNameTestFixture(
        test_id="tmuxp_yaml",
        path=".tmuxp.yaml",
        expect=False,
    ),
    PureNameTestFixture(
        test_id="parent_tmuxp_yaml",
        path="../.tmuxp.yaml",
        expect=False,
    ),
    PureNameTestFixture(
        test_id="parent_dir",
        path="../",
        expect=False,
    ),
    PureNameTestFixture(
        test_id="absolute_path",
        path="/hello/world",
        expect=False,
    ),
    PureNameTestFixture(
        test_id="home_tmuxp_path",
        path="~/.tmuxp/hey",
        expect=False,
    ),
    PureNameTestFixture(
        test_id="home_work_path",
        path="~/work/c/tmux/",
        expect=False,
    ),
    PureNameTestFixture(
        test_id="home_work_tmuxp_yaml",
        path="~/work/c/tmux/.tmuxp.yaml",
        expect=False,
    ),
    PureNameTestFixture(
        test_id="pure_name",
        path="myproject",
        expect=True,
    ),
]


@pytest.mark.parametrize(
    list(PureNameTestFixture._fields),
    PURE_NAME_TEST_FIXTURES,
    ids=[test.test_id for test in PURE_NAME_TEST_FIXTURES],
)
def test_is_pure_name(
    test_id: str,
    path: str,
    expect: bool,
) -> None:
    """Test is_pure_name() is truthy when file, not directory or config alias."""
    assert is_pure_name(path) == expect


def test_tmuxp_configdir_env_var(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests get_workspace_dir() when TMUXP_CONFIGDIR is set."""
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(tmp_path))

    assert get_workspace_dir() == str(tmp_path)


def test_tmuxp_configdir_xdg_config_dir(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_workspace_dir() when XDG_CONFIG_HOME is set."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    tmux_dir = tmp_path / "tmuxp"
    tmux_dir.mkdir()

    assert get_workspace_dir() == str(tmux_dir)


@pytest.fixture
def homedir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture to ensure and return a home directory."""
    home = tmp_path / "home"
    home.mkdir()
    return home


@pytest.fixture
def configdir(homedir: pathlib.Path) -> pathlib.Path:
    """Fixture to ensure user directory for tmuxp and return it, via homedir fixture."""
    conf = homedir / ".tmuxp"
    conf.mkdir()
    return conf


@pytest.fixture
def projectdir(homedir: pathlib.Path) -> pathlib.Path:
    """Fixture to ensure and return an example project dir."""
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
    """Test find_workspace_file() resolves dots as relative / current directory."""
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
    assert find_workspace_file(f"../../.tmuxp/{user_config_name}.yaml") == str(
        user_config,
    )
    assert find_workspace_file("myconfig") == str(user_config)
    assert find_workspace_file("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(FileNotFoundError):
        find_workspace_file(".tmuxp.json")
    with pytest.raises(FileNotFoundError):
        find_workspace_file(".tmuxp.ini")
    with pytest.raises(FileNotFoundError):
        find_workspace_file("../")
    with pytest.raises(FileNotFoundError):
        find_workspace_file("mooooooo")

    monkeypatch.chdir(homedir)

    expect = str(project_config)
    assert find_workspace_file("work/project") == expect
    assert find_workspace_file("work/project/") == expect
    assert find_workspace_file("./work/project") == expect
    assert find_workspace_file("./work/project/") == expect
    assert find_workspace_file(f".tmuxp/{user_config_name}.yaml") == str(user_config)
    assert find_workspace_file(f"./.tmuxp/{user_config_name}.yaml") == str(
        user_config,
    )
    assert find_workspace_file("myconfig") == str(user_config)
    assert find_workspace_file("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(FileNotFoundError):
        find_workspace_file("")
    with pytest.raises(FileNotFoundError):
        find_workspace_file(".")
    with pytest.raises(FileNotFoundError):
        find_workspace_file(".tmuxp.yaml")
    with pytest.raises(FileNotFoundError):
        find_workspace_file("../")
    with pytest.raises(FileNotFoundError):
        find_workspace_file("mooooooo")

    monkeypatch.chdir(configdir)

    expect = str(project_config)
    assert find_workspace_file("../work/project") == expect
    assert find_workspace_file("../../home/work/project") == expect
    assert find_workspace_file("../work/project/") == expect
    assert find_workspace_file(f"{user_config_name}.yaml") == str(user_config)
    assert find_workspace_file(f"./{user_config_name}.yaml") == str(user_config)
    assert find_workspace_file("myconfig") == str(user_config)
    assert find_workspace_file("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(FileNotFoundError):
        find_workspace_file("")
    with pytest.raises(FileNotFoundError):
        find_workspace_file(".")
    with pytest.raises(FileNotFoundError):
        find_workspace_file(".tmuxp.yaml")
    with pytest.raises(FileNotFoundError):
        find_workspace_file("../")
    with pytest.raises(FileNotFoundError):
        find_workspace_file("mooooooo")

    monkeypatch.chdir(tmp_path)

    expect = str(project_config)
    assert find_workspace_file("home/work/project") == expect
    assert find_workspace_file("./home/work/project/") == expect
    assert find_workspace_file(f"home/.tmuxp/{user_config_name}.yaml") == str(
        user_config,
    )
    assert find_workspace_file(f"./home/.tmuxp/{user_config_name}.yaml") == str(
        user_config,
    )
    assert find_workspace_file("myconfig") == str(user_config)
    assert find_workspace_file("~/.tmuxp/myconfig.yaml") == str(user_config)

    with pytest.raises(FileNotFoundError):
        find_workspace_file("")
    with pytest.raises(FileNotFoundError):
        find_workspace_file(".")
    with pytest.raises(FileNotFoundError):
        find_workspace_file(".tmuxp.yaml")
    with pytest.raises(FileNotFoundError):
        find_workspace_file("../")
    with pytest.raises(FileNotFoundError):
        find_workspace_file("mooooooo")


def test_find_workspace_file_arg(
    homedir: pathlib.Path,
    configdir: pathlib.Path,
    projectdir: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test find_workspace_file() via file path."""
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

    def check_cmd(config_arg: str) -> _pytest.capture.CaptureResult[str]:
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
    assert str(user_config) in check_cmd(f"../../.tmuxp/{user_config_name}.yaml").out
    assert user_config.stem in check_cmd("myconfig").out
    assert str(user_config) in check_cmd("~/.tmuxp/myconfig.yaml").out

    with pytest.raises(FileNotFoundError, match="file not found"):
        assert "file not found" in check_cmd(".tmuxp.json").err
    with pytest.raises(FileNotFoundError, match="file not found"):
        assert "file not found" in check_cmd(".tmuxp.ini").err
    with pytest.raises(FileNotFoundError, match="No tmuxp files found"):
        assert "No tmuxp files found" in check_cmd("../").err
    with pytest.raises(
        FileNotFoundError,
        match="workspace-file not found in workspace dir",
    ):
        assert "workspace-file not found in workspace dir" in check_cmd("moo").err


class GetWorkspaceDirCandidatesFixture(t.NamedTuple):
    """Test fixture for get_workspace_dir_candidates()."""

    test_id: str
    env_vars: dict[str, str]  # Relative to tmp_path
    dirs_to_create: list[str]  # Relative to tmp_path
    workspace_files: dict[str, int]  # dir -> count of .yaml files to create
    expected_active_suffix: str  # Suffix of active dir (e.g., ".tmuxp")
    expected_candidates_count: int


GET_WORKSPACE_DIR_CANDIDATES_FIXTURES: list[GetWorkspaceDirCandidatesFixture] = [
    GetWorkspaceDirCandidatesFixture(
        test_id="default_tmuxp_only",
        env_vars={},
        dirs_to_create=["home/.tmuxp"],
        workspace_files={"home/.tmuxp": 3},
        expected_active_suffix=".tmuxp",
        expected_candidates_count=2,  # ~/.config/tmuxp (not found) + ~/.tmuxp
    ),
    GetWorkspaceDirCandidatesFixture(
        test_id="xdg_exists_tmuxp_not",
        env_vars={"XDG_CONFIG_HOME": "home/.config"},
        dirs_to_create=["home/.config/tmuxp"],
        workspace_files={"home/.config/tmuxp": 2},
        expected_active_suffix="tmuxp",  # XDG takes precedence
        expected_candidates_count=2,
    ),
    GetWorkspaceDirCandidatesFixture(
        test_id="both_exist_xdg_wins",
        env_vars={"XDG_CONFIG_HOME": "home/.config"},
        dirs_to_create=["home/.config/tmuxp", "home/.tmuxp"],
        workspace_files={"home/.config/tmuxp": 2, "home/.tmuxp": 5},
        expected_active_suffix="tmuxp",  # XDG wins when both exist
        expected_candidates_count=2,
    ),
    GetWorkspaceDirCandidatesFixture(
        test_id="custom_configdir",
        env_vars={"TMUXP_CONFIGDIR": "custom/workspaces"},
        dirs_to_create=["custom/workspaces", "home/.tmuxp"],
        workspace_files={"custom/workspaces": 4},
        expected_active_suffix="workspaces",
        expected_candidates_count=3,  # custom + ~/.config/tmuxp + ~/.tmuxp
    ),
    GetWorkspaceDirCandidatesFixture(
        test_id="none_exist_fallback",
        env_vars={},
        dirs_to_create=[],  # No dirs created
        workspace_files={},
        expected_active_suffix=".tmuxp",  # Falls back to ~/.tmuxp
        expected_candidates_count=2,
    ),
]


@pytest.mark.parametrize(
    list(GetWorkspaceDirCandidatesFixture._fields),
    GET_WORKSPACE_DIR_CANDIDATES_FIXTURES,
    ids=[test.test_id for test in GET_WORKSPACE_DIR_CANDIDATES_FIXTURES],
)
def test_get_workspace_dir_candidates(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    env_vars: dict[str, str],
    dirs_to_create: list[str],
    workspace_files: dict[str, int],
    expected_active_suffix: str,
    expected_candidates_count: int,
) -> None:
    """Test get_workspace_dir_candidates() returns correct candidates."""
    # Setup home directory
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))

    # Clear any existing env vars that might interfere
    monkeypatch.delenv("TMUXP_CONFIGDIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    # Create directories
    for dir_path in dirs_to_create:
        (tmp_path / dir_path).mkdir(parents=True, exist_ok=True)

    # Create workspace files
    for dir_path, count in workspace_files.items():
        dir_full = tmp_path / dir_path
        for i in range(count):
            (dir_full / f"workspace{i}.yaml").touch()

    # Set environment variables (resolve relative paths)
    for var, path in env_vars.items():
        monkeypatch.setenv(var, str(tmp_path / path))

    # Get candidates
    candidates = get_workspace_dir_candidates()

    # Verify count
    assert len(candidates) == expected_candidates_count, (
        f"Expected {expected_candidates_count} candidates, got {len(candidates)}"
    )

    # Verify structure
    for candidate in candidates:
        assert "path" in candidate
        assert "source" in candidate
        assert "exists" in candidate
        assert "workspace_count" in candidate
        assert "active" in candidate

    # Verify exactly one is active
    active_candidates = [c for c in candidates if c["active"]]
    assert len(active_candidates) == 1, "Expected exactly one active candidate"

    # Verify active suffix
    active = active_candidates[0]
    assert active["path"].endswith(expected_active_suffix), (
        f"Expected active path to end with '{expected_active_suffix}', "
        f"got '{active['path']}'"
    )

    # Verify workspace counts for existing directories
    for candidate in candidates:
        if candidate["exists"]:
            # Find the matching dir in workspace_files by the last path component
            candidate_suffix = candidate["path"].split("/")[-1]
            for dir_path, expected_count in workspace_files.items():
                if dir_path.endswith(candidate_suffix):
                    assert candidate["workspace_count"] == expected_count, (
                        f"Expected {expected_count} workspaces in {candidate['path']}, "
                        f"got {candidate['workspace_count']}"
                    )
                    break  # Found match, stop checking


def test_get_workspace_dir_candidates_uses_private_path(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that get_workspace_dir_candidates() masks home directory with ~."""
    home = tmp_path / "home"
    tmuxp_dir = home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("TMUXP_CONFIGDIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    candidates = get_workspace_dir_candidates()

    # All paths should use ~ instead of full home path
    for candidate in candidates:
        path = candidate["path"]
        assert str(home) not in path, f"Path should be masked: {path}"
        assert path.startswith("~"), f"Path should start with ~: {path}"
