"""Test for tmuxp configuration import, inlining, expanding and export."""

from __future__ import annotations

import logging
import pathlib
import typing as t

import pytest

from tests.constants import EXAMPLE_PATH
from tmuxp import exc
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.workspace import loader, validation

if t.TYPE_CHECKING:
    from tests.fixtures.structures import WorkspaceTestData


def load_workspace(path: str | pathlib.Path) -> dict[str, t.Any]:
    """Load tmuxp workspace configuration from file."""
    return ConfigReader._from_file(
        pathlib.Path(path) if isinstance(path, str) else path,
    )


def test_export_json(
    tmp_path: pathlib.Path,
    config_fixture: WorkspaceTestData,
) -> None:
    """Test exporting configuration dictionary to JSON."""
    json_workspace_file = tmp_path / "config.json"

    configparser = ConfigReader(config_fixture.sample_workspace.sample_workspace_dict)

    json_workspace_data = configparser.dump("json", indent=2)

    json_workspace_file.write_text(json_workspace_data, encoding="utf-8")

    new_workspace_data = ConfigReader._from_file(path=json_workspace_file)
    assert config_fixture.sample_workspace.sample_workspace_dict == new_workspace_data


def test_workspace_expand1(config_fixture: WorkspaceTestData) -> None:
    """Expand shell commands from string to list."""
    test_workspace = loader.expand(config_fixture.expand1.before_workspace)
    assert test_workspace == config_fixture.expand1.after_workspace()


def test_workspace_expand2(config_fixture: WorkspaceTestData) -> None:
    """Expand shell commands from string to list."""
    unexpanded_dict = ConfigReader._load(
        fmt="yaml",
        content=config_fixture.expand2.unexpanded_yaml(),
    )
    expanded_dict = ConfigReader._load(
        fmt="yaml",
        content=config_fixture.expand2.expanded_yaml(),
    )
    assert loader.expand(unexpanded_dict) == expanded_dict


"""Test config inheritance for the nested 'start_command'."""

inheritance_workspace_before = {
    "session_name": "sample workspace",
    "start_directory": "/",
    "windows": [
        {
            "window_name": "editor",
            "start_directory": "~",
            "panes": [{"shell_command": ["vim"]}, {"shell_command": ['cowsay "hey"']}],
            "layout": "main-vertical",
        },
        {
            "window_name": "logging",
            "panes": [{"shell_command": ["tail -F /var/log/syslog"]}],
        },
        {"window_name": "shufu", "panes": [{"shell_command": ["htop"]}]},
        {"options": {"automatic-rename": True}, "panes": [{"shell_command": ["htop"]}]},
    ],
}

inheritance_workspace_after = {
    "session_name": "sample workspace",
    "start_directory": "/",
    "windows": [
        {
            "window_name": "editor",
            "start_directory": "~",
            "panes": [{"shell_command": ["vim"]}, {"shell_command": ['cowsay "hey"']}],
            "layout": "main-vertical",
        },
        {
            "window_name": "logging",
            "panes": [{"shell_command": ["tail -F /var/log/syslog"]}],
        },
        {"window_name": "shufu", "panes": [{"shell_command": ["htop"]}]},
        {"options": {"automatic-rename": True}, "panes": [{"shell_command": ["htop"]}]},
    ],
}


def test_inheritance_workspace() -> None:
    """TODO: Create a test to verify workspace config inheritance to object tree."""
    workspace = inheritance_workspace_before

    # TODO: Look at verifying window_start_directory
    # if 'start_directory' in workspace:
    #     session_start_directory = workspace['start_directory']
    # else:
    #     session_start_directory = None

    # for windowconfitem in workspace['windows']:
    #     window_start_directory = None
    #
    #     if 'start_directory' in windowconfitem:
    #         window_start_directory = windowconfitem['start_directory']
    #     elif session_start_directory:
    #         window_start_directory = session_start_directory
    #
    #     for paneconfitem in windowconfitem['panes']:
    #         if 'start_directory' in paneconfitem:
    #             pane_start_directory = paneconfitem['start_directory']
    #         elif window_start_directory:
    #             paneconfitem['start_directory'] = window_start_directory
    #         elif session_start_directory:
    #             paneconfitem['start_directory'] = session_start_directory

    assert workspace == inheritance_workspace_after


def test_shell_command_before(config_fixture: WorkspaceTestData) -> None:
    """Config inheritance for the nested 'start_command'."""
    test_workspace = config_fixture.shell_command_before.config_unexpanded
    test_workspace = loader.expand(test_workspace)

    assert test_workspace == config_fixture.shell_command_before.config_expanded()

    test_workspace = loader.trickle(test_workspace)
    assert test_workspace == config_fixture.shell_command_before.config_after()


def test_in_session_scope(config_fixture: WorkspaceTestData) -> None:
    """Verify shell_command before_session is in session scope."""
    sconfig = ConfigReader._load(
        fmt="yaml",
        content=config_fixture.shell_command_before_session.before,
    )

    validation.validate_schema(sconfig)

    assert loader.expand(sconfig) == sconfig
    assert loader.expand(loader.trickle(sconfig)) == ConfigReader._load(
        fmt="yaml",
        content=config_fixture.shell_command_before_session.expected,
    )


def test_trickle_relative_start_directory(config_fixture: WorkspaceTestData) -> None:
    """Verify tmuxp config proliferates relative start directory to descendants."""
    test_workspace = loader.trickle(config_fixture.trickle.before)
    assert test_workspace == config_fixture.trickle.expected


def test_trickle_window_with_no_pane_workspace() -> None:
    """Verify tmuxp window config automatically infers a single pane."""
    test_yaml = """
    session_name: test_session
    windows:
    - window_name: test_1
      panes:
      - shell_command:
        - ls -l
    - window_name: test_no_panes
    """
    sconfig = ConfigReader._load(fmt="yaml", content=test_yaml)
    validation.validate_schema(sconfig)

    assert loader.expand(loader.trickle(sconfig))["windows"][1]["panes"][0] == {
        "shell_command": [],
    }


def test_expands_blank_panes(config_fixture: WorkspaceTestData) -> None:
    """Expand blank config into full form.

    Handle ``NoneType`` and 'blank'::

    # nothing, None, 'blank'
    'panes': [
        None,
        'blank'
    ]

    # should be blank
    'panes': [
        'shell_command': []
    ]

    Blank strings::

        panes: [
            ''
        ]

        # should output to:
        panes:
            'shell_command': ['']

    """
    yaml_workspace_file = EXAMPLE_PATH / "blank-panes.yaml"
    test_workspace = load_workspace(yaml_workspace_file)
    assert loader.expand(test_workspace) == config_fixture.expand_blank.expected


def test_no_session_name() -> None:
    """Verify exception raised when tmuxp configuration has no session name."""
    yaml_workspace = """
    - window_name: editor
      panes:
      shell_command:
      - tail -F /var/log/syslog
      start_directory: /var/log
    - window_name: logging
      automatic-rename: true
      panes:
      - shell_command:
      - htop
    """

    sconfig = ConfigReader._load(fmt="yaml", content=yaml_workspace)

    with pytest.raises(exc.WorkspaceError) as excinfo:
        validation.validate_schema(sconfig)
        assert excinfo.match(r'requires "session_name"')


def test_no_windows() -> None:
    """Verify exception raised when tmuxp configuration has no windows."""
    yaml_workspace = """
    session_name: test session
    """

    sconfig = ConfigReader._load(fmt="yaml", content=yaml_workspace)

    with pytest.raises(exc.WorkspaceError) as excinfo:
        validation.validate_schema(sconfig)
        assert excinfo.match(r'list of "windows"')


def test_no_window_name() -> None:
    """Verify exception raised when tmuxp config missing window name."""
    yaml_workspace = """
    session_name: test session
    windows:
    - window_name: editor
      panes:
      shell_command:
      - tail -F /var/log/syslog
      start_directory: /var/log
    - automatic-rename: true
      panes:
      - shell_command:
      - htop
    """

    sconfig = ConfigReader._load(fmt="yaml", content=yaml_workspace)

    with pytest.raises(exc.WorkspaceError) as excinfo:
        validation.validate_schema(sconfig)
        assert excinfo.match('missing "window_name"')


def test_replaces_env_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading configuration resolves environmental variables."""
    env_key = "TESTHEY92"
    env_val = "HEYO1"
    yaml_workspace = """
    start_directory: {TEST_VAR}/test
    shell_command_before: {TEST_VAR}/test2
    before_script: {TEST_VAR}/test3
    session_name: hi - {TEST_VAR}
    options:
        default-command: {TEST_VAR}/lol
    global_options:
        default-shell: {TEST_VAR}/moo
    windows:
    - window_name: editor
      panes:
      - shell_command:
      - tail -F /var/log/syslog
      start_directory: /var/log
    - window_name: logging @ {TEST_VAR}
      automatic-rename: true
      panes:
      - shell_command:
      - htop
    """.format(TEST_VAR=f"${{{env_key}}}")

    sconfig = ConfigReader._load(fmt="yaml", content=yaml_workspace)

    monkeypatch.setenv(str(env_key), str(env_val))
    sconfig = loader.expand(sconfig)
    assert f"{env_val}/test" == sconfig["start_directory"]
    assert (
        f"{env_val}/test2" in sconfig["shell_command_before"]["shell_command"][0]["cmd"]
    )
    assert f"{env_val}/test3" == sconfig["before_script"]
    assert f"hi - {env_val}" == sconfig["session_name"]
    assert f"{env_val}/moo" == sconfig["global_options"]["default-shell"]
    assert f"{env_val}/lol" == sconfig["options"]["default-command"]
    assert f"logging @ {env_val}" == sconfig["windows"][1]["window_name"]


def test_validate_plugins() -> None:
    """Test validation of plugins loading via tmuxp configuration file."""
    yaml_workspace = """
    session_name: test session
    plugins: tmuxp-plugin-one.plugin.TestPluginOne
    windows:
    - window_name: editor
      panes:
      shell_command:
      - tail -F /var/log/syslog
      start_directory: /var/log
    """

    sconfig = ConfigReader._load(fmt="yaml", content=yaml_workspace)

    with pytest.raises(exc.WorkspaceError) as excinfo:
        validation.validate_schema(sconfig)
        assert excinfo.match("only supports list type")


class SynchronizeFixture(t.NamedTuple):
    """Fixture for synchronize shorthand expansion."""

    test_id: str
    synchronize: bool | str
    expected_section: str | None


SYNCHRONIZE_FIXTURES: list[SynchronizeFixture] = [
    SynchronizeFixture(
        test_id="true-enables-before",
        synchronize=True,
        expected_section="options",
    ),
    SynchronizeFixture(
        test_id="before-enables-before",
        synchronize="before",
        expected_section="options",
    ),
    SynchronizeFixture(
        test_id="after-enables-after",
        synchronize="after",
        expected_section="options_after",
    ),
    SynchronizeFixture(
        test_id="false-only-removes-key",
        synchronize=False,
        expected_section=None,
    ),
]


@pytest.mark.parametrize(
    list(SynchronizeFixture._fields),
    SYNCHRONIZE_FIXTURES,
    ids=[fixture.test_id for fixture in SYNCHRONIZE_FIXTURES],
)
def test_expand_synchronize(
    test_id: str,
    synchronize: bool | str,
    expected_section: str | None,
) -> None:
    """expand() desugars synchronize into tmux window options."""
    workspace: dict[str, t.Any] = {
        "session_name": f"sync-{test_id}",
        "windows": [
            {
                "window_name": "main",
                "synchronize": synchronize,
                "panes": [{"shell_command": ["echo hi"]}],
            },
        ],
    }

    result = loader.expand(workspace)
    window = result["windows"][0]

    assert "synchronize" not in window
    if expected_section is None:
        assert "synchronize-panes" not in window.get("options", {})
        assert "synchronize-panes" not in window.get("options_after", {})
    else:
        assert window[expected_section]["synchronize-panes"] == "on"


class ShellCommandAfterFixture(t.NamedTuple):
    """Fixture for shell_command_after expansion."""

    test_id: str
    shell_command_after: str | list[str]
    expected_commands: list[str]


SHELL_COMMAND_AFTER_FIXTURES: list[ShellCommandAfterFixture] = [
    ShellCommandAfterFixture(
        test_id="string-command",
        shell_command_after="echo done",
        expected_commands=["echo done"],
    ),
    ShellCommandAfterFixture(
        test_id="list-commands",
        shell_command_after=["echo done", "echo bye"],
        expected_commands=["echo done", "echo bye"],
    ),
]


@pytest.mark.parametrize(
    list(ShellCommandAfterFixture._fields),
    SHELL_COMMAND_AFTER_FIXTURES,
    ids=[fixture.test_id for fixture in SHELL_COMMAND_AFTER_FIXTURES],
)
def test_expand_shell_command_after(
    test_id: str,
    shell_command_after: str | list[str],
    expected_commands: list[str],
) -> None:
    """expand() normalizes shell_command_after like shell_command_before."""
    workspace: dict[str, t.Any] = {
        "session_name": f"after-{test_id}",
        "windows": [
            {
                "window_name": "main",
                "shell_command_after": shell_command_after,
                "panes": [{"shell_command": ["echo hi"]}],
            },
        ],
    }

    result = loader.expand(workspace)
    after = result["windows"][0]["shell_command_after"]

    assert [cmd["cmd"] for cmd in after["shell_command"]] == expected_commands


class PaneTitleFixture(t.NamedTuple):
    """Fixture for pane title option expansion."""

    test_id: str
    enabled: bool
    position: str | None
    expected_position: str | None
    expect_warning: bool


PANE_TITLE_FIXTURES: list[PaneTitleFixture] = [
    PaneTitleFixture(
        test_id="enabled-defaults",
        enabled=True,
        position=None,
        expected_position="top",
        expect_warning=False,
    ),
    PaneTitleFixture(
        test_id="enabled-bottom",
        enabled=True,
        position="bottom",
        expected_position="bottom",
        expect_warning=False,
    ),
    PaneTitleFixture(
        test_id="enabled-invalid-falls-back",
        enabled=True,
        position="invalid",
        expected_position="top",
        expect_warning=True,
    ),
    PaneTitleFixture(
        test_id="disabled-removes-session-keys",
        enabled=False,
        position="bottom",
        expected_position=None,
        expect_warning=False,
    ),
]


@pytest.mark.parametrize(
    list(PaneTitleFixture._fields),
    PANE_TITLE_FIXTURES,
    ids=[fixture.test_id for fixture in PANE_TITLE_FIXTURES],
)
def test_expand_pane_titles(
    caplog: pytest.LogCaptureFixture,
    test_id: str,
    enabled: bool,
    position: str | None,
    expected_position: str | None,
    expect_warning: bool,
) -> None:
    """expand() turns session pane title keys into tmux window options."""
    workspace: dict[str, t.Any] = {
        "session_name": f"title-{test_id}",
        "enable_pane_titles": enabled,
        "pane_title_format": " #T ",
        "windows": [
            {
                "window_name": "main",
                "panes": [
                    {"title": "editor", "shell_command": ["echo hi"]},
                    {"shell_command": ["echo bye"]},
                ],
            },
        ],
    }
    if position is not None:
        workspace["pane_title_position"] = position

    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.loader"):
        result = loader.expand(workspace)

    window = result["windows"][0]
    assert "enable_pane_titles" not in result
    assert "pane_title_position" not in result
    assert "pane_title_format" not in result
    assert window["panes"][0]["title"] == "editor"

    if expected_position is None:
        assert "pane-border-status" not in window.get("options", {})
    else:
        assert window["options"]["pane-border-status"] == expected_position
        assert window["options"]["pane-border-format"] == " #T "

    position_warnings = [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING and hasattr(record, "tmux_session")
    ]
    assert bool(position_warnings) is expect_warning
    if expect_warning:
        assert position_warnings[0].tmux_session == f"title-{test_id}"


def test_expand_logs_debug(
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """expand() logs DEBUG with tmux_session extra."""
    workspace = {"session_name": "test_expand", "windows": [{"window_name": "main"}]}
    with caplog.at_level(logging.DEBUG, logger="tmuxp.workspace.loader"):
        loader.expand(workspace, cwd=str(tmp_path))
    records = [r for r in caplog.records if r.msg == "expanding workspace config"]
    assert len(records) >= 1
    assert getattr(records[0], "tmux_session", None) == "test_expand"


def test_trickle_logs_debug(
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """trickle() logs DEBUG with tmux_session extra."""
    workspace = {
        "session_name": "test_trickle",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    with caplog.at_level(logging.DEBUG, logger="tmuxp.workspace.loader"):
        loader.trickle(workspace)
    records = [
        r for r in caplog.records if r.msg == "trickling down workspace defaults"
    ]
    assert len(records) >= 1
    assert getattr(records[0], "tmux_session", None) == "test_trickle"


def test_validate_schema_logs_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """validate_schema() logs DEBUG with tmux_session extra."""
    workspace = {
        "session_name": "test_validate",
        "windows": [{"window_name": "main"}],
    }
    with caplog.at_level(logging.DEBUG, logger="tmuxp.workspace.validation"):
        validation.validate_schema(workspace)
    records = [r for r in caplog.records if r.msg == "validating workspace schema"]
    assert len(records) >= 1
    assert getattr(records[0], "tmux_session", None) == "test_validate"


class LifecycleHookExpandFixture(t.NamedTuple):
    """Fixture for lifecycle hook expansion."""

    test_id: str
    hook_key: str
    hook_value: str | list[str]
    env: dict[str, str]
    expected: str | list[str]


LIFECYCLE_HOOK_EXPAND_FIXTURES: list[LifecycleHookExpandFixture] = [
    LifecycleHookExpandFixture(
        test_id="start-string-env",
        hook_key="on_project_start",
        hook_value="$TMUXP_HOOK_CMD",
        env={"TMUXP_HOOK_CMD": "docker compose up"},
        expected="docker compose up",
    ),
    LifecycleHookExpandFixture(
        test_id="stop-string-with-suffix",
        hook_key="on_project_stop",
        hook_value="$TMUXP_HOOK_CMD down",
        env={"TMUXP_HOOK_CMD": "docker compose"},
        expected="docker compose down",
    ),
    LifecycleHookExpandFixture(
        test_id="restart-list-env",
        hook_key="on_project_restart",
        hook_value=["$TMUXP_HOOK_CMD", "echo world"],
        env={"TMUXP_HOOK_CMD": "echo hello"},
        expected=["echo hello", "echo world"],
    ),
]


@pytest.mark.parametrize(
    list(LifecycleHookExpandFixture._fields),
    LIFECYCLE_HOOK_EXPAND_FIXTURES,
    ids=[fixture.test_id for fixture in LIFECYCLE_HOOK_EXPAND_FIXTURES],
)
def test_expand_lifecycle_hooks(
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    hook_key: str,
    hook_value: str | list[str],
    env: dict[str, str],
    expected: str | list[str],
) -> None:
    """expand() expands environment variables in lifecycle hook values."""
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    workspace: dict[str, t.Any] = {
        "session_name": f"hook-{test_id}",
        hook_key: hook_value,
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }

    result = loader.expand(workspace)

    assert result[hook_key] == expected
