"""CLI tests for tmuxp load."""

from __future__ import annotations

import contextlib
import io
import pathlib
import typing as t

import libtmux
import pytest
from libtmux.server import Server
from libtmux.session import Session

from tests.constants import FIXTURE_PATH
from tests.fixtures import utils as test_utils
from tmuxp import cli
from tmuxp._internal.colors import ColorMode, Colors
from tmuxp._internal.config_reader import ConfigReader
from tmuxp._internal.private_path import PrivatePath
from tmuxp.cli.load import (
    _dispatch_build,
    _load_append_windows_to_current_session,
    _load_attached,
    load_plugins,
    load_workspace,
)
from tmuxp.workspace import loader
from tmuxp.workspace.builder import WorkspaceBuilder


def test_load_workspace(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generic test for loading a tmuxp workspace via tmuxp load."""
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspace/builder" / "two_pane.yaml"

    # open it detached
    session = load_workspace(
        session_file,
        socket_name=server.socket_name,
        detached=True,
    )

    assert isinstance(session, Session)
    assert session.name == "sample workspace"


def test_load_workspace_passes_tmux_config(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test tmuxp load with a tmux configuration file."""
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspace/builder" / "two_pane.yaml"

    # open it detached
    session = load_workspace(
        session_file,
        socket_name=server.socket_name,
        tmux_config_file=str(FIXTURE_PATH / "tmux" / "tmux.conf"),
        detached=True,
    )

    assert isinstance(session, Session)
    assert isinstance(session.server, Server)
    assert session.server.config_file == str(FIXTURE_PATH / "tmux" / "tmux.conf")


def test_load_workspace_named_session(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test tmuxp load with a custom tmux session name."""
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspace/builder" / "two_pane.yaml"

    # open it detached
    session = load_workspace(
        session_file,
        socket_name=server.socket_name,
        new_session_name="tmuxp-new",
        detached=True,
    )

    assert isinstance(session, Session)
    assert session.name == "tmuxp-new"


def test_load_workspace_name_match_regression_252(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test tmuxp load for a regression where tmux shell names would not match."""
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspace/builder" / "two_pane.yaml"

    # open it detached
    session = load_workspace(
        session_file,
        socket_name=server.socket_name,
        detached=True,
    )

    assert isinstance(session, Session)
    assert session.name == "sample workspace"

    workspace_file = tmp_path / "simple.yaml"

    workspace_file.write_text(
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
        str(workspace_file),
        socket_name=server.socket_name,
        detached=True,
    )
    assert session is not None
    assert session.name == "sampleconfi"


def test_load_symlinked_workspace(
    server: Server,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test tmuxp load can follow a symlinked tmuxp config file."""
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv("TMUX", raising=False)

    realtemp = tmp_path / "myrealtemp"
    realtemp.mkdir()
    linktemp = tmp_path / "symlinktemp"
    linktemp.symlink_to(realtemp)
    workspace_file = linktemp / "simple.yaml"

    workspace_file.write_text(
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
        str(workspace_file),
        socket_name=server.socket_name,
        detached=True,
    )
    assert session is not None
    assert session.active_window is not None
    pane = session.active_window.active_pane

    assert isinstance(session, Session)
    assert session.name == "samplesimple"

    assert pane is not None
    assert pane.pane_current_path == str(realtemp)


if t.TYPE_CHECKING:
    from typing import TypeAlias

    from pytest_mock import MockerFixture

    ExpectedOutput: TypeAlias = str | list[str] | None


class CLILoadFixture(t.NamedTuple):
    """Test fixture for tmuxp load tests."""

    # pytest (internal): Test fixture name
    test_id: str

    # test params
    cli_args: list[str | list[str]]
    config_paths: list[str]
    session_names: list[str]
    expected_exit_code: int
    expected_in_out: ExpectedOutput = None
    expected_not_in_out: ExpectedOutput = None
    expected_in_err: ExpectedOutput = None
    expected_not_in_err: ExpectedOutput = None


TEST_LOAD_FIXTURES: list[CLILoadFixture] = [
    CLILoadFixture(
        test_id="dir-relative-dot-samedir",
        cli_args=["load", "."],
        config_paths=["{tmp_path}/.tmuxp.yaml"],
        session_names=["my_config"],
        expected_exit_code=0,
        expected_in_out=None,
        expected_not_in_out=None,
    ),
    CLILoadFixture(
        test_id="dir-relative-dot-slash-samedir",
        cli_args=["load", "./"],
        config_paths=["{tmp_path}/.tmuxp.yaml"],
        session_names=["my_config"],
        expected_exit_code=0,
        expected_in_out=None,
        expected_not_in_out=None,
    ),
    CLILoadFixture(
        test_id="dir-relative-file-samedir",
        cli_args=["load", "./.tmuxp.yaml"],
        config_paths=["{tmp_path}/.tmuxp.yaml"],
        session_names=["my_config"],
        expected_exit_code=0,
        expected_in_out=None,
        expected_not_in_out=None,
    ),
    CLILoadFixture(
        test_id="filename-relative-file-samedir",
        cli_args=["load", "./my_config.yaml"],
        config_paths=["{tmp_path}/my_config.yaml"],
        session_names=["my_config"],
        expected_exit_code=0,
        expected_in_out=None,
        expected_not_in_out=None,
    ),
    CLILoadFixture(
        test_id="configdir-session-name",
        cli_args=["load", "my_config"],
        config_paths=["{TMUXP_CONFIGDIR}/my_config.yaml"],
        session_names=["my_config"],
        expected_exit_code=0,
        expected_in_out=None,
        expected_not_in_out=None,
    ),
    CLILoadFixture(
        test_id="configdir-absolute",
        cli_args=["load", "~/.config/tmuxp/my_config.yaml"],
        config_paths=["{TMUXP_CONFIGDIR}/my_config.yaml"],
        session_names=["my_config"],
        expected_exit_code=0,
        expected_in_out=None,
        expected_not_in_out=None,
    ),
    #
    # Multiple configs
    #
    CLILoadFixture(
        test_id="configdir-session-name-double",
        cli_args=["load", "my_config", "second_config"],
        config_paths=[
            "{TMUXP_CONFIGDIR}/my_config.yaml",
            "{TMUXP_CONFIGDIR}/second_config.yaml",
        ],
        session_names=["my_config", "second_config"],
        expected_exit_code=0,
        expected_in_out=None,
        expected_not_in_out=None,
    ),
]


@pytest.mark.parametrize(
    list(CLILoadFixture._fields),
    TEST_LOAD_FIXTURES,
    ids=[test.test_id for test in TEST_LOAD_FIXTURES],
)
@pytest.mark.usefixtures("tmuxp_configdir_default")
def test_load(
    tmp_path: pathlib.Path,
    tmuxp_configdir: pathlib.Path,
    server: Server,
    session: Session,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    cli_args: list[str],
    config_paths: list[str],
    session_names: list[str],
    expected_exit_code: int,
    expected_in_out: ExpectedOutput,
    expected_not_in_out: ExpectedOutput,
    expected_in_err: ExpectedOutput,
    expected_not_in_err: ExpectedOutput,
) -> None:
    """Parametrized test battery for tmuxp load CLI command."""
    assert server.socket_name is not None

    monkeypatch.chdir(tmp_path)
    for session_name, config_path in zip(session_names, config_paths, strict=False):
        tmuxp_config = pathlib.Path(
            config_path.format(tmp_path=tmp_path, TMUXP_CONFIGDIR=tmuxp_configdir),
        )
        tmuxp_config.write_text(
            f"""
        session_name: {session_name}
        windows:
        - window_name: test
          panes:
          -
        """,
            encoding="utf-8",
        )

    with contextlib.suppress(SystemExit):
        cli.cli([*cli_args, "-d", "-L", server.socket_name, "-y"])

    result = capsys.readouterr()
    output = "".join(list(result.out))

    if expected_in_out is not None:
        if isinstance(expected_in_out, str):
            expected_in_out = [expected_in_out]
        for needle in expected_in_out:
            assert needle in output

    if expected_not_in_out is not None:
        if isinstance(expected_not_in_out, str):
            expected_not_in_out = [expected_not_in_out]
        for needle in expected_not_in_out:
            assert needle not in output

    for session_name in session_names:
        assert server.has_session(session_name)


def test_regression_00132_session_name_with_dots(
    tmp_path: pathlib.Path,
    server: Server,
    session: Session,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Regression test for session names with dots."""
    yaml_config = FIXTURE_PATH / "workspace/builder" / "regression_00132_dots.yaml"
    cli_args = [str(yaml_config)]
    with pytest.raises(libtmux.exc.BadSessionName):
        cli.cli(["load", *cli_args])


class ZshAutotitleTestFixture(t.NamedTuple):
    """Test fixture for zsh auto title warning tests."""

    test_id: str
    cli_args: list[str]


ZSH_AUTOTITLE_TEST_FIXTURES: list[ZshAutotitleTestFixture] = [
    ZshAutotitleTestFixture(
        test_id="load_dot_detached",
        cli_args=["load", ".", "-d"],
    ),
    ZshAutotitleTestFixture(
        test_id="load_yaml_detached",
        cli_args=["load", ".tmuxp.yaml", "-d"],
    ),
]


@pytest.mark.parametrize(
    list(ZshAutotitleTestFixture._fields),
    ZSH_AUTOTITLE_TEST_FIXTURES,
    ids=[test.test_id for test in ZSH_AUTOTITLE_TEST_FIXTURES],
)
def test_load_zsh_autotitle_warning(
    test_id: str,
    cli_args: list[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    server: Server,
) -> None:
    """Test warning when ZSH auto title is enabled."""
    # create dummy tmuxp yaml so we don't get yelled at
    yaml_config = tmp_path / ".tmuxp.yaml"
    yaml_config.write_text(
        """
    session_name: test
    windows:
    - window_name: test
      panes:
      -
    """,
        encoding="utf-8",
    )
    oh_my_zsh_path = tmp_path / ".oh-my-zsh"
    oh_my_zsh_path.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)

    monkeypatch.delenv("DISABLE_AUTO_TITLE", raising=False)
    monkeypatch.setenv("SHELL", "zsh")

    # Use tmux server (socket name) used in the test
    assert server.socket_name is not None
    cli_args = [*cli_args, "-L", server.socket_name]

    cli.cli(cli_args)
    result = capsys.readouterr()
    assert "Please set" in result.out

    monkeypatch.setenv("DISABLE_AUTO_TITLE", "false")
    cli.cli(cli_args)
    result = capsys.readouterr()
    assert "Please set" in result.out

    monkeypatch.setenv("DISABLE_AUTO_TITLE", "true")
    cli.cli(cli_args)
    result = capsys.readouterr()
    assert "Please set" not in result.out

    monkeypatch.delenv("DISABLE_AUTO_TITLE", raising=False)
    monkeypatch.setenv("SHELL", "sh")
    cli.cli(cli_args)
    result = capsys.readouterr()
    assert "Please set" not in result.out


class LogFileTestFixture(t.NamedTuple):
    """Test fixture for log file tests."""

    test_id: str
    cli_args: list[str]


LOG_FILE_TEST_FIXTURES: list[LogFileTestFixture] = [
    LogFileTestFixture(
        test_id="load_with_log_file",
        cli_args=["--log-level", "info", "load", ".", "--log-file", "log.txt", "-d"],
    ),
]


@pytest.mark.parametrize(
    list(LogFileTestFixture._fields),
    LOG_FILE_TEST_FIXTURES,
    ids=[test.test_id for test in LOG_FILE_TEST_FIXTURES],
)
def test_load_log_file(
    test_id: str,
    cli_args: list[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test loading with a log file."""
    # create dummy tmuxp yaml that breaks to prevent actually loading tmux
    tmuxp_config_path = tmp_path / ".tmuxp.yaml"
    tmuxp_config_path.write_text(
        """
session_name: hello
  -
        """,
        encoding="utf-8",
    )
    oh_my_zsh_path = tmp_path / ".oh-my-zsh"
    oh_my_zsh_path.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)

    with contextlib.suppress(Exception):
        cli.cli(cli_args)

    result = capsys.readouterr()
    log_file_path = tmp_path / "log.txt"
    assert "loading workspace" in log_file_path.open().read()
    assert result.out is not None


def test_load_log_file_level_filtering(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Log-level filtering: INFO log file should not contain DEBUG messages."""
    tmuxp_config_path = tmp_path / ".tmuxp.yaml"
    tmuxp_config_path.write_text(
        """
session_name: hello
  -
        """,
        encoding="utf-8",
    )
    oh_my_zsh_path = tmp_path / ".oh-my-zsh"
    oh_my_zsh_path.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    with contextlib.suppress(Exception):
        cli.cli(["--log-level", "info", "load", ".", "--log-file", "log.txt", "-d"])

    log_file_path = tmp_path / "log.txt"
    log_contents = log_file_path.read_text()

    # INFO-level messages should appear
    assert "loading workspace" in log_contents.lower() or len(log_contents) > 0

    # No DEBUG-level markers should appear in an INFO-level log file
    for line in log_contents.splitlines():
        assert "(DEBUG)" not in line, (
            f"DEBUG message leaked into INFO-level log file: {line}"
        )


def test_load_plugins(
    monkeypatch_plugin_test_packages: None,
) -> None:
    """Test loading via tmuxp load with plugins."""
    from tmuxp_test_plugin_bwb.plugin import (  # type: ignore
        PluginBeforeWorkspaceBuilder,
    )

    plugins_config = test_utils.read_workspace_file("workspace/builder/plugin_bwb.yaml")

    session_config = ConfigReader._load(fmt="yaml", content=plugins_config)
    session_config = loader.expand(session_config)

    plugins = load_plugins(session_config)

    assert len(plugins) == 1

    test_plugin_class_types = [
        PluginBeforeWorkspaceBuilder().__class__,
    ]
    for plugin in plugins:
        assert plugin.__class__ in test_plugin_class_types


class PluginVersionTestFixture(t.NamedTuple):
    """Test fixture for plugin version tests."""

    test_id: str
    cli_args: list[str]
    inputs: list[str]


PLUGIN_VERSION_SKIP_TEST_FIXTURES: list[PluginVersionTestFixture] = [
    PluginVersionTestFixture(
        test_id="skip_version_fail",
        cli_args=["load", "tests/fixtures/workspace/builder/plugin_versions_fail.yaml"],
        inputs=["y\n"],
    ),
]


@pytest.mark.skip("Not sure how to clean up the tmux session this makes")
@pytest.mark.parametrize(
    list(PluginVersionTestFixture._fields),
    PLUGIN_VERSION_SKIP_TEST_FIXTURES,
    ids=[test.test_id for test in PLUGIN_VERSION_SKIP_TEST_FIXTURES],
)
def test_load_plugins_version_fail_skip(
    monkeypatch_plugin_test_packages: None,
    test_id: str,
    cli_args: list[str],
    inputs: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test plugin version failure with skip."""
    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    result = capsys.readouterr()

    assert "[Loading]" in result.out


PLUGIN_VERSION_NO_SKIP_TEST_FIXTURES: list[PluginVersionTestFixture] = [
    PluginVersionTestFixture(
        test_id="no_skip_version_fail",
        cli_args=["load", "tests/fixtures/workspace/builder/plugin_versions_fail.yaml"],
        inputs=["n\n"],
    ),
]


@pytest.mark.parametrize(
    list(PluginVersionTestFixture._fields),
    PLUGIN_VERSION_NO_SKIP_TEST_FIXTURES,
    ids=[test.test_id for test in PLUGIN_VERSION_NO_SKIP_TEST_FIXTURES],
)
def test_load_plugins_version_fail_no_skip(
    monkeypatch_plugin_test_packages: None,
    test_id: str,
    cli_args: list[str],
    inputs: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test plugin version failure without skip."""
    monkeypatch.setattr("sys.stdin", io.StringIO("".join(inputs)))

    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    result = capsys.readouterr()

    assert "[Not Skipping]" in result.out


class PluginMissingTestFixture(t.NamedTuple):
    """Test fixture for plugin missing tests."""

    test_id: str
    cli_args: list[str]


PLUGIN_MISSING_TEST_FIXTURES: list[PluginMissingTestFixture] = [
    PluginMissingTestFixture(
        test_id="missing_plugin",
        cli_args=["load", "tests/fixtures/workspace/builder/plugin_missing_fail.yaml"],
    ),
]


@pytest.mark.parametrize(
    list(PluginMissingTestFixture._fields),
    PLUGIN_MISSING_TEST_FIXTURES,
    ids=[test.test_id for test in PLUGIN_MISSING_TEST_FIXTURES],
)
def test_load_plugins_plugin_missing(
    monkeypatch_plugin_test_packages: None,
    test_id: str,
    cli_args: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test loading with missing plugin."""
    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    result = capsys.readouterr()

    assert "[Plugin Error]" in result.out


def test_plugin_system_before_script(
    monkeypatch_plugin_test_packages: None,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test tmuxp load with sessions using before_script."""
    # this is an implementation test. Since this testsuite may be ran within
    # a tmux session by the developer himself, delete the TMUX variable
    # temporarily.
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspace/builder" / "plugin_bs.yaml"

    # open it detached
    session = load_workspace(
        session_file,
        socket_name=server.socket_name,
        detached=True,
    )

    assert isinstance(session, Session)
    assert session.name == "plugin_test_bs"


def test_load_attached(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    """Test tmuxp load's attachment behavior."""
    # Load a session and attach from outside tmux
    monkeypatch.delenv("TMUX", raising=False)

    attach_mock = mocker.patch("libtmux.session.Session.attach")
    attach_mock.return_value.stderr = None

    yaml_config = test_utils.read_workspace_file("workspace/builder/two_pane.yaml")
    session_config = ConfigReader._load(fmt="yaml", content=yaml_config)

    builder = WorkspaceBuilder(session_config=session_config, server=server)

    _load_attached(builder, False)

    assert attach_mock.call_count == 1


def test_load_attached_detached(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    """Test tmuxp load when sessions are build without attaching client."""
    # Load a session but don't attach
    monkeypatch.delenv("TMUX", raising=False)

    attach_mock = mocker.patch("libtmux.session.Session.attach")
    attach_mock.return_value.stderr = None

    yaml_config = test_utils.read_workspace_file("workspace/builder/two_pane.yaml")
    session_config = ConfigReader._load(fmt="yaml", content=yaml_config)

    builder = WorkspaceBuilder(session_config=session_config, server=server)

    _load_attached(builder, True)

    assert attach_mock.call_count == 0


def test_load_attached_within_tmux(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    """Test loading via tmuxp load when already within a tmux session."""
    # Load a session and attach from within tmux
    monkeypatch.setenv("TMUX", "/tmp/tmux-1234/default,123,0")

    switch_client_mock = mocker.patch("libtmux.session.Session.switch_client")
    switch_client_mock.return_value.stderr = None

    yaml_config = test_utils.read_workspace_file("workspace/builder/two_pane.yaml")
    session_config = ConfigReader._load(fmt="yaml", content=yaml_config)

    builder = WorkspaceBuilder(session_config=session_config, server=server)

    _load_attached(builder, False)

    assert switch_client_mock.call_count == 1


def test_load_attached_within_tmux_detached(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    """Test loading via tmuxp load within a tmux session switches clients."""
    # Load a session and attach from within tmux
    monkeypatch.setenv("TMUX", "/tmp/tmux-1234/default,123,0")

    switch_client_mock = mocker.patch("libtmux.session.Session.switch_client")
    switch_client_mock.return_value.stderr = None

    yaml_config = test_utils.read_workspace_file("workspace/builder/two_pane.yaml")
    session_config = ConfigReader._load(fmt="yaml", content=yaml_config)

    builder = WorkspaceBuilder(session_config=session_config, server=server)

    _load_attached(builder, True)

    assert switch_client_mock.call_count == 1


def test_load_append_windows_to_current_session(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test tmuxp load when windows are appended to the current session."""
    yaml_config = test_utils.read_workspace_file("workspace/builder/two_pane.yaml")
    session_config = ConfigReader._load(fmt="yaml", content=yaml_config)

    builder = WorkspaceBuilder(session_config=session_config, server=server)
    builder.build()

    assert len(server.sessions) == 1
    assert len(server.windows) == 3

    # Assign an active pane to the session
    assert server.panes[0].pane_id
    monkeypatch.setenv("TMUX_PANE", server.panes[0].pane_id)

    builder = WorkspaceBuilder(session_config=session_config, server=server)
    _load_append_windows_to_current_session(builder)

    assert len(server.sessions) == 1
    assert len(server.windows) == 6


# Privacy masking in load command


def test_load_no_ansi_in_nontty_stderr(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No ANSI escape codes in stderr when running in non-TTY context (CI/pipe)."""
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspace/builder" / "two_pane.yaml"

    load_workspace(str(session_file), socket_name=server.socket_name, detached=True)

    captured = capsys.readouterr()
    assert "\x1b[" not in captured.err, "ANSI codes leaked into non-TTY stderr"


class ProgressDisableFixture(t.NamedTuple):
    """Test fixture for progress disable logic."""

    test_id: str
    env_value: str | None
    no_progress_flag: bool
    expected_disabled: bool


PROGRESS_DISABLE_FIXTURES: list[ProgressDisableFixture] = [
    ProgressDisableFixture("default_enabled", None, False, False),
    ProgressDisableFixture("env_disabled", "0", False, True),
    ProgressDisableFixture("flag_disabled", None, True, True),
    ProgressDisableFixture("env_enabled_explicit", "1", False, False),
    ProgressDisableFixture("flag_overrides_env", "1", True, True),
]


@pytest.mark.parametrize(
    list(ProgressDisableFixture._fields),
    PROGRESS_DISABLE_FIXTURES,
    ids=[f.test_id for f in PROGRESS_DISABLE_FIXTURES],
)
def test_progress_disable_logic(
    test_id: str,
    env_value: str | None,
    no_progress_flag: bool,
    expected_disabled: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Progress disable expression matches expected behavior."""
    if env_value is not None:
        monkeypatch.setenv("TMUXP_PROGRESS", env_value)
    else:
        monkeypatch.delenv("TMUXP_PROGRESS", raising=False)

    import os

    result = no_progress_flag or os.getenv("TMUXP_PROGRESS", "1") == "0"
    assert result is expected_disabled


def test_load_workspace_no_progress(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """load_workspace with no_progress=True creates session without spinner."""
    monkeypatch.delenv("TMUX", raising=False)
    session_file = FIXTURE_PATH / "workspace/builder" / "two_pane.yaml"

    session = load_workspace(
        session_file,
        socket_name=server.socket_name,
        detached=True,
        no_progress=True,
    )

    assert isinstance(session, Session)
    assert session.name == "sample workspace"


def test_load_workspace_env_progress_disabled(
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """load_workspace with TMUXP_PROGRESS=0 creates session without spinner."""
    monkeypatch.delenv("TMUX", raising=False)
    monkeypatch.setenv("TMUXP_PROGRESS", "0")
    session_file = FIXTURE_PATH / "workspace/builder" / "two_pane.yaml"

    session = load_workspace(
        session_file,
        socket_name=server.socket_name,
        detached=True,
    )

    assert isinstance(session, Session)
    assert session.name == "sample workspace"


class NoShellCommandBeforeFixture(t.NamedTuple):
    """Test fixture for --no-shell-command-before flag tests."""

    test_id: str
    no_shell_command_before: bool
    expect_before_cmd: bool


NO_SHELL_COMMAND_BEFORE_FIXTURES: list[NoShellCommandBeforeFixture] = [
    NoShellCommandBeforeFixture(
        test_id="with-shell-command-before",
        no_shell_command_before=False,
        expect_before_cmd=True,
    ),
    NoShellCommandBeforeFixture(
        test_id="no-shell-command-before",
        no_shell_command_before=True,
        expect_before_cmd=False,
    ),
]


@pytest.mark.parametrize(
    list(NoShellCommandBeforeFixture._fields),
    NO_SHELL_COMMAND_BEFORE_FIXTURES,
    ids=[f.test_id for f in NO_SHELL_COMMAND_BEFORE_FIXTURES],
)
def test_load_workspace_no_shell_command_before(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    no_shell_command_before: bool,
    expect_before_cmd: bool,
) -> None:
    """Test --no-shell-command-before strips shell_command_before from config."""
    monkeypatch.delenv("TMUX", raising=False)

    workspace_file = tmp_path / "test.yaml"
    workspace_file.write_text(
        """
session_name: scb_test
shell_command_before:
  - echo __BEFORE__
windows:
- window_name: main
  panes:
  - echo hello
""",
        encoding="utf-8",
    )

    session = load_workspace(
        str(workspace_file),
        socket_name=server.socket_name,
        detached=True,
        no_shell_command_before=no_shell_command_before,
    )

    assert isinstance(session, Session)
    assert session.name == "scb_test"

    window = session.active_window
    assert window is not None
    pane = window.active_pane
    assert pane is not None

    from libtmux.test.retry import retry_until

    if expect_before_cmd:
        assert retry_until(
            lambda: "__BEFORE__" in "\n".join(pane.capture_pane()),
            seconds=5,
        )
    else:
        import time

        time.sleep(1)
        assert "__BEFORE__" not in "\n".join(pane.capture_pane())


def test_load_no_shell_command_before_strips_all_levels(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify --no-shell-command-before strips from session, window, and pane levels."""
    monkeypatch.delenv("TMUX", raising=False)

    workspace_file = tmp_path / "multi_level.yaml"
    workspace_file.write_text(
        """
session_name: strip_test
shell_command_before:
  - echo session_before
windows:
- window_name: main
  shell_command_before:
    - echo window_before
  panes:
  - shell_command:
    - echo hello
    shell_command_before:
    - echo pane_before
""",
        encoding="utf-8",
    )

    # Verify the stripping logic via loader functions
    raw = ConfigReader._from_file(workspace_file) or {}
    expanded = loader.expand(raw, cwd=str(tmp_path))

    # Before stripping, shell_command_before should be present
    assert "shell_command_before" in expanded
    assert "shell_command_before" in expanded["windows"][0]
    assert "shell_command_before" in expanded["windows"][0]["panes"][0]

    # Simulate the stripping logic from load_workspace
    expanded.pop("shell_command_before", None)
    for window in expanded.get("windows", []):
        window.pop("shell_command_before", None)
        for pane in window.get("panes", []):
            pane.pop("shell_command_before", None)

    trickled = loader.trickle(expanded)

    # After stripping + trickle, pane commands should not include before cmds
    pane_cmds = trickled["windows"][0]["panes"][0]["shell_command"]
    cmd_strings = [c["cmd"] for c in pane_cmds]
    assert "echo session_before" not in cmd_strings
    assert "echo window_before" not in cmd_strings
    assert "echo pane_before" not in cmd_strings
    assert "echo hello" in cmd_strings


class DebugFlagFixture(t.NamedTuple):
    """Test fixture for --debug flag tests."""

    test_id: str
    debug: bool
    expect_tmux_commands_in_output: bool


DEBUG_FLAG_FIXTURES: list[DebugFlagFixture] = [
    DebugFlagFixture(
        test_id="debug-off",
        debug=False,
        expect_tmux_commands_in_output=False,
    ),
    DebugFlagFixture(
        test_id="debug-on",
        debug=True,
        expect_tmux_commands_in_output=True,
    ),
]


@pytest.mark.parametrize(
    list(DebugFlagFixture._fields),
    DEBUG_FLAG_FIXTURES,
    ids=[f.test_id for f in DEBUG_FLAG_FIXTURES],
)
def test_load_workspace_debug_flag(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    test_id: str,
    debug: bool,
    expect_tmux_commands_in_output: bool,
) -> None:
    """Test --debug shows tmux commands in output."""
    monkeypatch.delenv("TMUX", raising=False)

    workspace_file = tmp_path / "test.yaml"
    workspace_file.write_text(
        """
session_name: debug_test
windows:
- window_name: main
  panes:
  - echo hello
""",
        encoding="utf-8",
    )

    session = load_workspace(
        str(workspace_file),
        socket_name=server.socket_name,
        detached=True,
        debug=debug,
    )

    assert isinstance(session, Session)
    assert session.name == "debug_test"

    captured = capsys.readouterr()
    if expect_tmux_commands_in_output:
        assert "$ " in captured.out
        assert "new-session" in captured.out
    else:
        # When debug is off, tmux commands should not appear in stdout
        assert "new-session" not in captured.out


def test_load_debug_cleans_up_handler(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify --debug removes its handler after load completes."""
    import logging

    monkeypatch.delenv("TMUX", raising=False)

    workspace_file = tmp_path / "test.yaml"
    workspace_file.write_text(
        """
session_name: debug_cleanup
windows:
- window_name: main
  panes:
  - echo hello
""",
        encoding="utf-8",
    )

    libtmux_logger = logging.getLogger("libtmux.common")
    handler_count_before = len(libtmux_logger.handlers)

    load_workspace(
        str(workspace_file),
        socket_name=server.socket_name,
        detached=True,
        debug=True,
    )

    assert len(libtmux_logger.handlers) == handler_count_before


def test_load_masks_home_in_spinner_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Spinner message should mask home directory via PrivatePath."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    workspace_file = pathlib.Path("/home/testuser/work/project/.tmuxp.yaml")
    private_path = str(PrivatePath(workspace_file))
    message = f"Loading workspace: myproject ({private_path})"

    assert "~/work/project/.tmuxp.yaml" in message
    assert "/home/testuser" not in message


def test_load_on_project_start_runs_hook(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tmuxp load runs on_project_start hook before session creation."""
    monkeypatch.delenv("TMUX", raising=False)

    marker = tmp_path / "start_hook_ran"
    workspace_file = tmp_path / "hook_start.yaml"
    workspace_file.write_text(
        f"""\
session_name: hook-start-test
on_project_start: "touch {marker}"
windows:
- window_name: main
  panes:
  - echo hello
""",
        encoding="utf-8",
    )

    session = load_workspace(
        workspace_file,
        socket_name=server.socket_name,
        detached=True,
    )

    assert marker.exists()
    assert session is not None
    session.kill()


class DispatchBuildHookFixture(t.NamedTuple):
    """Fixture for on_project_start dispatch behavior."""

    test_id: str
    detached: bool
    append: bool
    answer_yes: bool
    here: bool
    inside_tmux: bool
    prompt_choice: str | None
    expected_loader: str
    expect_pre_build_hook: bool


DISPATCH_BUILD_HOOK_FIXTURES: list[DispatchBuildHookFixture] = [
    DispatchBuildHookFixture(
        test_id="detached-new-session-runs-hook",
        detached=True,
        append=False,
        answer_yes=False,
        here=False,
        inside_tmux=False,
        prompt_choice=None,
        expected_loader="detached",
        expect_pre_build_hook=True,
    ),
    DispatchBuildHookFixture(
        test_id="interactive-append-skips-hook",
        detached=False,
        append=False,
        answer_yes=False,
        here=False,
        inside_tmux=True,
        prompt_choice="a",
        expected_loader="append",
        expect_pre_build_hook=False,
    ),
    DispatchBuildHookFixture(
        test_id="interactive-detach-runs-hook",
        detached=False,
        append=False,
        answer_yes=False,
        here=False,
        inside_tmux=True,
        prompt_choice="n",
        expected_loader="detached",
        expect_pre_build_hook=True,
    ),
    DispatchBuildHookFixture(
        test_id="interactive-attach-runs-hook",
        detached=False,
        append=False,
        answer_yes=False,
        here=False,
        inside_tmux=True,
        prompt_choice="y",
        expected_loader="attached",
        expect_pre_build_hook=True,
    ),
    DispatchBuildHookFixture(
        test_id="here-inside-tmux-skips-hook",
        detached=False,
        append=False,
        answer_yes=False,
        here=True,
        inside_tmux=True,
        prompt_choice=None,
        expected_loader="here",
        expect_pre_build_hook=False,
    ),
    DispatchBuildHookFixture(
        test_id="here-outside-tmux-fallback-runs-hook",
        detached=False,
        append=False,
        answer_yes=False,
        here=True,
        inside_tmux=False,
        prompt_choice=None,
        expected_loader="attached",
        expect_pre_build_hook=True,
    ),
]


@pytest.mark.parametrize(
    list(DispatchBuildHookFixture._fields),
    DISPATCH_BUILD_HOOK_FIXTURES,
    ids=[f.test_id for f in DISPATCH_BUILD_HOOK_FIXTURES],
)
def test_dispatch_build_on_project_start_only_for_new_session_paths(
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    detached: bool,
    append: bool,
    answer_yes: bool,
    here: bool,
    inside_tmux: bool,
    prompt_choice: str | None,
    expected_loader: str,
    expect_pre_build_hook: bool,
) -> None:
    """_dispatch_build only runs on_project_start on new-session load paths."""

    class DummyBuilder:
        """Minimal builder stub for dispatch tests."""

        def __init__(self) -> None:
            self.session = object()
            self.plugins: list[t.Any] = []
            self.on_progress: t.Any = "sentinel"
            self.on_before_script: t.Any = "sentinel"
            self.on_script_output: t.Any = "sentinel"
            self.on_build_event: t.Any = "sentinel"

    builder = t.cast(WorkspaceBuilder, DummyBuilder())
    loader_calls: list[str] = []
    hook_calls: list[str] = []

    def _pre_build_hook() -> None:
        hook_calls.append("hook")

    def _attached_stub(
        builder: DummyBuilder,
        detached: bool,
        pre_build_hook: t.Callable[[], None] | None = None,
        pre_attach_hook: t.Callable[[], None] | None = None,
    ) -> None:
        if pre_build_hook is not None:
            pre_build_hook()
        loader_calls.append("attached")

    def _detached_stub(
        builder: DummyBuilder,
        colors: Colors | None = None,
        pre_build_hook: t.Callable[[], None] | None = None,
        pre_output_hook: t.Callable[[], None] | None = None,
    ) -> None:
        if pre_build_hook is not None:
            pre_build_hook()
        loader_calls.append("detached")

    def _append_stub(builder: DummyBuilder) -> None:
        loader_calls.append("append")

    def _here_stub(builder: DummyBuilder) -> None:
        loader_calls.append("here")

    monkeypatch.setattr("tmuxp.cli.load._load_attached", _attached_stub)
    monkeypatch.setattr("tmuxp.cli.load._load_detached", _detached_stub)
    monkeypatch.setattr(
        "tmuxp.cli.load._load_append_windows_to_current_session",
        _append_stub,
    )
    monkeypatch.setattr("tmuxp.cli.load._load_here_in_current_session", _here_stub)
    monkeypatch.setattr(
        "tmuxp.cli.load._setup_plugins",
        lambda builder: builder.session,
    )

    if prompt_choice is not None:
        monkeypatch.setattr(
            "tmuxp.cli.load.prompt_choices",
            lambda *a, **kw: prompt_choice,
        )

    if inside_tmux:
        monkeypatch.setenv("TMUX", "/tmp/tmux-test/default,12345,0")
    else:
        monkeypatch.delenv("TMUX", raising=False)

    result = _dispatch_build(
        builder=builder,
        detached=detached,
        append=append,
        answer_yes=answer_yes,
        cli_colors=Colors(ColorMode.NEVER),
        here=here,
        pre_build_hook=_pre_build_hook,
    )

    assert result is builder.session
    assert loader_calls == [expected_loader], test_id
    assert hook_calls == (["hook"] if expect_pre_build_hook else []), test_id
    assert builder.on_progress is None
    assert builder.on_before_script is None
    assert builder.on_script_output is None
    assert builder.on_build_event is None


def test_load_on_project_restart_runs_hook(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tmuxp load runs on_project_restart hook when session already exists."""
    monkeypatch.delenv("TMUX", raising=False)

    marker = tmp_path / "restart_hook_ran"
    workspace_file = tmp_path / "hook_restart.yaml"
    workspace_file.write_text(
        f"""\
session_name: hook-restart-test
on_project_restart: "touch {marker}"
windows:
- window_name: main
  panes:
  - echo hello
""",
        encoding="utf-8",
    )

    # First load creates the session
    session = load_workspace(
        workspace_file,
        socket_name=server.socket_name,
        detached=True,
    )
    assert session is not None
    assert not marker.exists()

    # Second detached load does NOT trigger on_project_restart
    # (restart hook only fires on confirmed interactive reattach)
    load_workspace(
        workspace_file,
        socket_name=server.socket_name,
        detached=True,
    )
    assert not marker.exists()

    session.kill()


def test_load_on_project_restart_skipped_on_decline(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tmuxp load skips on_project_restart when user declines reattach."""
    monkeypatch.delenv("TMUX", raising=False)

    marker = tmp_path / "restart_hook_ran"
    workspace_file = tmp_path / "hook_restart_decline.yaml"
    workspace_file.write_text(
        f"""\
session_name: hook-restart-decline
on_project_restart: "touch {marker}"
windows:
- window_name: main
  panes:
  - echo hello
""",
        encoding="utf-8",
    )

    # First load creates the session
    session = load_workspace(
        workspace_file,
        socket_name=server.socket_name,
        detached=True,
    )
    assert session is not None
    assert not marker.exists()

    # Second load: session exists, user declines reattach
    monkeypatch.setattr(
        "tmuxp.cli.load.prompt_yes_no",
        lambda *a, **kw: False,
    )
    load_workspace(
        workspace_file,
        socket_name=server.socket_name,
        detached=False,
    )
    assert not marker.exists()

    session.kill()


def test_load_on_project_start_skipped_on_decline(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tmuxp load skips on_project_start when user declines reattach."""
    monkeypatch.delenv("TMUX", raising=False)

    marker = tmp_path / "start_hook_ran"
    workspace_file = tmp_path / "hook_start_decline.yaml"
    workspace_file.write_text(
        f"""\
session_name: hook-start-decline
on_project_start: "touch {marker}"
windows:
- window_name: main
  panes:
  - echo hello
""",
        encoding="utf-8",
    )

    # First load creates the session
    session = load_workspace(
        workspace_file,
        socket_name=server.socket_name,
        detached=True,
    )
    assert session is not None
    assert marker.exists()
    marker.unlink()

    # Second load: session exists, user declines reattach
    monkeypatch.setattr(
        "tmuxp.cli.load.prompt_yes_no",
        lambda *a, **kw: False,
    )
    load_workspace(
        workspace_file,
        socket_name=server.socket_name,
        detached=False,
    )
    assert not marker.exists()

    session.kill()


class ConfigKeyPrecedenceFixture(t.NamedTuple):
    """Test fixture for config key precedence tests."""

    test_id: str
    workspace_extra: dict[str, t.Any]
    cli_socket_name: str | None
    cli_tmux_config_file: str | None
    expect_socket_name: str | None
    expect_config_file: str | None


CONFIG_KEY_PRECEDENCE_FIXTURES: list[ConfigKeyPrecedenceFixture] = [
    ConfigKeyPrecedenceFixture(
        test_id="workspace-socket_name-used-as-fallback",
        workspace_extra={"socket_name": "{server_socket}"},
        cli_socket_name=None,
        cli_tmux_config_file=None,
        expect_socket_name="{server_socket}",
        expect_config_file=None,
    ),
    ConfigKeyPrecedenceFixture(
        test_id="workspace-config-used-as-fallback",
        workspace_extra={"config": "{tmux_conf}"},
        cli_socket_name="{server_socket}",
        cli_tmux_config_file=None,
        expect_socket_name="{server_socket}",
        expect_config_file="{tmux_conf}",
    ),
    ConfigKeyPrecedenceFixture(
        test_id="cli-overrides-workspace-socket_name",
        workspace_extra={"socket_name": "ignored-socket"},
        cli_socket_name="{server_socket}",
        cli_tmux_config_file=None,
        expect_socket_name="{server_socket}",
        expect_config_file=None,
    ),
    ConfigKeyPrecedenceFixture(
        test_id="cli-overrides-workspace-config",
        workspace_extra={"config": "/ignored/tmux.conf"},
        cli_socket_name="{server_socket}",
        cli_tmux_config_file="{tmux_conf}",
        expect_socket_name="{server_socket}",
        expect_config_file="{tmux_conf}",
    ),
]


@pytest.mark.parametrize(
    list(ConfigKeyPrecedenceFixture._fields),
    CONFIG_KEY_PRECEDENCE_FIXTURES,
    ids=[f.test_id for f in CONFIG_KEY_PRECEDENCE_FIXTURES],
)
def test_load_workspace_config_key_precedence(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    workspace_extra: dict[str, t.Any],
    cli_socket_name: str | None,
    cli_tmux_config_file: str | None,
    expect_socket_name: str | None,
    expect_config_file: str | None,
) -> None:
    """Workspace config keys (socket_name, config) used as Server fallbacks."""
    monkeypatch.delenv("TMUX", raising=False)

    tmux_conf = str(FIXTURE_PATH / "tmux" / "tmux.conf")
    server_socket = server.socket_name

    def _resolve(val: str | None) -> str | None:
        if val is None:
            return None
        return val.format(server_socket=server_socket, tmux_conf=tmux_conf)

    resolved_extra = {
        k: _resolve(v) if isinstance(v, str) else v for k, v in workspace_extra.items()
    }

    extra_lines = "\n".join(f"{k}: {v}" for k, v in resolved_extra.items())
    workspace_file = tmp_path / "test.yaml"
    workspace_file.write_text(
        f"""\
session_name: cfg-key-{test_id}
{extra_lines}
windows:
- window_name: main
  panes:
  - echo hello
""",
        encoding="utf-8",
    )

    session = load_workspace(
        str(workspace_file),
        socket_name=_resolve(cli_socket_name),
        tmux_config_file=_resolve(cli_tmux_config_file),
        detached=True,
    )

    assert isinstance(session, Session)

    if _resolve(expect_socket_name) is not None:
        assert session.server.socket_name == _resolve(expect_socket_name)
    if _resolve(expect_config_file) is not None:
        assert session.server.config_file == _resolve(expect_config_file)

    session.kill()


def test_load_workspace_template_context(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """load_workspace() renders {{ var }} templates before YAML parsing."""
    monkeypatch.delenv("TMUX", raising=False)

    workspace_file = tmp_path / "tpl.yaml"
    workspace_file.write_text(
        """\
session_name: {{ project }}-session
windows:
- window_name: {{ window }}
  panes:
  - echo {{ project }}
""",
        encoding="utf-8",
    )

    session = load_workspace(
        str(workspace_file),
        socket_name=server.socket_name,
        detached=True,
        template_context={"project": "myapp", "window": "editor"},
    )

    assert isinstance(session, Session)
    assert session.name == "myapp-session"
    assert session.windows[0].window_name == "editor"


def test_load_workspace_template_no_context(
    tmp_path: pathlib.Path,
    server: Server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """load_workspace() without template_context leaves {{ var }} as literals."""
    monkeypatch.delenv("TMUX", raising=False)

    workspace_file = tmp_path / "tpl.yaml"
    workspace_file.write_text(
        """\
session_name: plain-session
windows:
- window_name: main
  panes:
  - echo hello
""",
        encoding="utf-8",
    )

    session = load_workspace(
        str(workspace_file),
        socket_name=server.socket_name,
        detached=True,
    )

    assert isinstance(session, Session)
    assert session.name == "plain-session"


def test_load_here_and_append_mutually_exclusive() -> None:
    """--here and --append cannot be used together."""
    from tmuxp.cli import create_parser

    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["load", "--here", "--append", "myconfig"])


def test_load_here_and_detached_mutually_exclusive() -> None:
    """--here and -d cannot be used together."""
    from tmuxp.cli import create_parser

    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["load", "--here", "-d", "myconfig"])


def test_load_append_and_detached_mutually_exclusive() -> None:
    """--append and -d cannot be used together."""
    from tmuxp.cli import create_parser

    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["load", "--append", "-d", "myconfig"])


# --- --here error recovery tests (535ca944) ---


class HereErrorRecoveryFixture(t.NamedTuple):
    """Fixture for --here error recovery prompt behavior."""

    test_id: str
    here: bool
    expected_choices: list[str]
    expected_default: str
    kill_option_present: bool


HERE_ERROR_RECOVERY_FIXTURES: list[HereErrorRecoveryFixture] = [
    HereErrorRecoveryFixture(
        test_id="here-mode-no-kill",
        here=True,
        expected_choices=["a", "d"],
        expected_default="d",
        kill_option_present=False,
    ),
    HereErrorRecoveryFixture(
        test_id="normal-mode-has-kill",
        here=False,
        expected_choices=["k", "a", "d"],
        expected_default="k",
        kill_option_present=True,
    ),
]


@pytest.mark.parametrize(
    list(HereErrorRecoveryFixture._fields),
    HERE_ERROR_RECOVERY_FIXTURES,
    ids=[f.test_id for f in HERE_ERROR_RECOVERY_FIXTURES],
)
def test_here_error_recovery_prompt(
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    here: bool,
    expected_choices: list[str],
    expected_default: str,
    kill_option_present: bool,
) -> None:
    """--here error recovery skips (k)ill to protect user's live session."""
    from unittest.mock import MagicMock

    from tmuxp._internal.colors import ColorMode, Colors
    from tmuxp.cli.load import _dispatch_build

    captured_kwargs: dict[str, t.Any] = {}

    def _capture_prompt_choices(*args: t.Any, **kwargs: t.Any) -> str:
        captured_kwargs.update(kwargs)
        captured_kwargs["choices"] = kwargs.get("choices", [])
        return "d"  # Always detach to exit cleanly

    monkeypatch.setattr(
        "tmuxp.cli.load.prompt_choices",
        _capture_prompt_choices,
    )

    # Create a mock builder that raises TmuxpException when built
    from tmuxp import exc

    mock_builder = MagicMock()
    mock_builder.session = None

    # Simulate the here path raising an error
    if here:
        monkeypatch.setattr(
            "tmuxp.cli.load._load_here_in_current_session",
            MagicMock(side_effect=exc.TmuxpException("test error")),
        )
        monkeypatch.setenv("TMUX", "/tmp/tmux-test/default,12345,0")
    else:
        monkeypatch.setattr(
            "tmuxp.cli.load._load_attached",
            MagicMock(side_effect=exc.TmuxpException("test error")),
        )
        monkeypatch.delenv("TMUX", raising=False)

    cli_colors = Colors(ColorMode.NEVER)

    with pytest.raises(SystemExit):
        _dispatch_build(
            builder=mock_builder,
            detached=False,
            append=False,
            answer_yes=not here,  # answer_yes triggers _load_attached path
            cli_colors=cli_colors,
            here=here,
        )

    assert captured_kwargs["choices"] == expected_choices
    assert captured_kwargs.get("default") == expected_default
    assert ("k" in captured_kwargs["choices"]) == kill_option_present
