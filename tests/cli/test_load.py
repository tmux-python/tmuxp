"""CLI tests for tmuxp load."""
import contextlib
import io
import pathlib
import typing as t

import libtmux
import pytest
from libtmux.common import has_lt_version
from libtmux.server import Server
from libtmux.session import Session
from pytest_mock import MockerFixture

from tmuxp import cli
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.cli.load import (
    _load_append_windows_to_current_session,
    _load_attached,
    load_plugins,
    load_workspace,
)
from tmuxp.workspace import loader
from tmuxp.workspace.builder import WorkspaceBuilder

from ..constants import FIXTURE_PATH
from ..fixtures import utils as test_utils


def test_load_workspace(
    server: "Server",
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
    server: "Server",
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
    server: "Server",
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


@pytest.mark.skipif(
    has_lt_version("2.1"),
    reason="exact session name matches only tmux >= 2.1",
)
def test_load_workspace_name_match_regression_252(
    tmp_path: pathlib.Path,
    server: "Server",
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
    server: "Server",
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
    assert session.attached_window is not None
    pane = session.attached_window.attached_pane

    assert isinstance(session, Session)
    assert session.name == "samplesimple"

    assert pane is not None
    assert pane.pane_current_path == str(realtemp)


if t.TYPE_CHECKING:
    from typing_extensions import TypeAlias

    ExpectedOutput: TypeAlias = t.Optional[t.Union[str, t.List[str]]]


class CLILoadFixture(t.NamedTuple):
    """Test fixture for tmuxp load tests."""

    # pytest (internal): Test fixture name
    test_id: str

    # test params
    cli_args: t.List[t.Union[str, t.List[str]]]
    config_paths: t.List[str]
    session_names: t.List[str]
    expected_exit_code: int
    expected_in_out: "ExpectedOutput" = None
    expected_not_in_out: "ExpectedOutput" = None
    expected_in_err: "ExpectedOutput" = None
    expected_not_in_err: "ExpectedOutput" = None


TEST_LOAD_FIXTURES: t.List[CLILoadFixture] = [
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
    server: "Server",
    session: Session,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    cli_args: t.List[str],
    config_paths: t.List[str],
    session_names: t.List[str],
    expected_exit_code: int,
    expected_in_out: "ExpectedOutput",
    expected_not_in_out: "ExpectedOutput",
    expected_in_err: "ExpectedOutput",
    expected_not_in_err: "ExpectedOutput",
) -> None:
    """Parametrized test battery for tmuxp load CLI command."""
    assert server.socket_name is not None

    monkeypatch.chdir(tmp_path)
    for session_name, config_path in zip(session_names, config_paths):
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
    server: "Server",
    session: Session,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Regression test for session names with dots."""
    yaml_config = FIXTURE_PATH / "workspace/builder" / "regression_00132_dots.yaml"
    cli_args = [str(yaml_config)]
    with pytest.raises(libtmux.exc.BadSessionName):
        cli.cli(["load", *cli_args])


@pytest.mark.parametrize(
    "cli_args",
    [["load", ".", "-d"], ["load", ".tmuxp.yaml", "-d"]],
)
def test_load_zsh_autotitle_warning(
    cli_args: t.List[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    server: "Server",
) -> None:
    """Test loading ZSH without DISABLE_AUTO_TITLE raises warning."""
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


@pytest.mark.parametrize(
    "cli_args",
    [
        (["load", ".", "--log-file", "log.txt", "-d"]),
    ],
)
def test_load_log_file(
    cli_args: t.List[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test loading via tmuxp load with --log-file."""
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
    assert "Loading" in log_file_path.open().read()
    assert result.out is not None


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


@pytest.mark.skip("Not sure how to clean up the tmux session this makes")
@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (
            ["load", "tests/fixtures/workspace/builder/plugin_versions_fail.yaml"],
            ["y\n"],
        ),
    ],
)
def test_load_plugins_version_fail_skip(
    monkeypatch_plugin_test_packages: None,
    cli_args: t.List[str],
    inputs: t.List[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test tmuxp load with plugins failing version constraints can continue."""
    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    result = capsys.readouterr()

    assert "[Loading]" in result.out


@pytest.mark.parametrize(
    "cli_args,inputs",
    [
        (
            ["load", "tests/fixtures/workspace/builder/plugin_versions_fail.yaml"],
            ["n\n"],
        ),
    ],
)
def test_load_plugins_version_fail_no_skip(
    monkeypatch_plugin_test_packages: None,
    cli_args: t.List[str],
    inputs: t.List[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test tmuxp load with plugins failing version constraints can exit."""
    monkeypatch.setattr("sys.stdin", io.StringIO("".join(inputs)))

    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    result = capsys.readouterr()

    assert "[Not Skipping]" in result.out


@pytest.mark.parametrize(
    "cli_args",
    [(["load", "tests/fixtures/workspace/builder/plugin_missing_fail.yaml"])],
)
def test_load_plugins_plugin_missing(
    monkeypatch_plugin_test_packages: None,
    cli_args: t.List[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test tmuxp load with plugins missing raise an error."""
    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    result = capsys.readouterr()

    assert "[Plugin Error]" in result.out


def test_plugin_system_before_script(
    monkeypatch_plugin_test_packages: None,
    server: "Server",
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
    server: "Server",
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    """Test tmuxp load's attachment behavior."""
    # Load a session and attach from outside tmux
    monkeypatch.delenv("TMUX", raising=False)

    attach_session_mock = mocker.patch("libtmux.session.Session.attach_session")
    attach_session_mock.return_value.stderr = None

    yaml_config = test_utils.read_workspace_file("workspace/builder/two_pane.yaml")
    session_config = ConfigReader._load(fmt="yaml", content=yaml_config)

    builder = WorkspaceBuilder(session_config=session_config, server=server)

    _load_attached(builder, False)

    assert attach_session_mock.call_count == 1


def test_load_attached_detached(
    server: "Server",
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    """Test tmuxp load when sessions are build without attaching client."""
    # Load a session but don't attach
    monkeypatch.delenv("TMUX", raising=False)

    attach_session_mock = mocker.patch("libtmux.session.Session.attach_session")
    attach_session_mock.return_value.stderr = None

    yaml_config = test_utils.read_workspace_file("workspace/builder/two_pane.yaml")
    session_config = ConfigReader._load(fmt="yaml", content=yaml_config)

    builder = WorkspaceBuilder(session_config=session_config, server=server)

    _load_attached(builder, True)

    assert attach_session_mock.call_count == 0


def test_load_attached_within_tmux(
    server: "Server",
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
    server: "Server",
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
    server: "Server",
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
