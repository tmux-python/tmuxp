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


def test_expand_synchronize() -> None:
    """Test that expand() desugars synchronize into options/options_after."""
    workspace = {
        "session_name": "test",
        "windows": [
            {
                "window_name": "before",
                "synchronize": True,
                "panes": [{"shell_command": ["echo hi"]}],
            },
            {
                "window_name": "after",
                "synchronize": "after",
                "panes": [{"shell_command": ["echo hi"]}],
            },
            {
                "window_name": "false",
                "synchronize": False,
                "panes": [{"shell_command": ["echo hi"]}],
            },
        ],
    }
    result = loader.expand(workspace)

    # synchronize: True → options with synchronize-panes on, key removed
    assert "synchronize" not in result["windows"][0]
    assert result["windows"][0]["options"]["synchronize-panes"] == "on"

    # synchronize: "after" → options_after with synchronize-panes on, key removed
    assert "synchronize" not in result["windows"][1]
    assert result["windows"][1]["options_after"]["synchronize-panes"] == "on"

    # synchronize: False → no options added, key removed
    assert "synchronize" not in result["windows"][2]
    assert "options" not in result["windows"][2] or "synchronize-panes" not in result[
        "windows"
    ][2].get("options", {})


def test_expand_shell_command_after() -> None:
    """Test that expand() normalizes shell_command_after into expanded form."""
    workspace = {
        "session_name": "test",
        "windows": [
            {
                "window_name": "with-after",
                "shell_command_after": ["echo done", "echo bye"],
                "panes": [{"shell_command": ["echo hi"]}],
            },
            {
                "window_name": "string-after",
                "shell_command_after": "echo single",
                "panes": [{"shell_command": ["echo hi"]}],
            },
            {
                "window_name": "no-after",
                "panes": [{"shell_command": ["echo hi"]}],
            },
        ],
    }
    result = loader.expand(workspace)

    # List form: normalized to {shell_command: [{cmd: "..."}, ...]}
    after = result["windows"][0]["shell_command_after"]
    assert isinstance(after, dict)
    assert len(after["shell_command"]) == 2
    assert after["shell_command"][0]["cmd"] == "echo done"
    assert after["shell_command"][1]["cmd"] == "echo bye"

    # String form: normalized the same way
    after_str = result["windows"][1]["shell_command_after"]
    assert isinstance(after_str, dict)
    assert len(after_str["shell_command"]) == 1
    assert after_str["shell_command"][0]["cmd"] == "echo single"

    # No shell_command_after: key absent
    assert "shell_command_after" not in result["windows"][2]


def test_expand_pane_titles() -> None:
    """Test that expand() desugars pane title session keys into window options."""
    workspace = {
        "session_name": "test",
        "enable_pane_titles": True,
        "pane_title_position": "bottom",
        "pane_title_format": " #T ",
        "windows": [
            {
                "window_name": "w1",
                "panes": [
                    {"title": "editor", "shell_command": ["echo hi"]},
                    {"shell_command": ["echo bye"]},
                ],
            },
            {
                "window_name": "w2",
                "options": {"pane-border-status": "off"},
                "panes": [{"shell_command": ["echo hi"]}],
            },
        ],
    }
    result = loader.expand(workspace)

    # Session-level keys removed
    assert "enable_pane_titles" not in result
    assert "pane_title_position" not in result
    assert "pane_title_format" not in result

    # Window 1: options populated from session-level config
    assert result["windows"][0]["options"]["pane-border-status"] == "bottom"
    assert result["windows"][0]["options"]["pane-border-format"] == " #T "

    # Window 2: per-window override preserved (setdefault doesn't overwrite)
    assert result["windows"][1]["options"]["pane-border-status"] == "off"
    assert result["windows"][1]["options"]["pane-border-format"] == " #T "

    # Pane title key preserved for builder
    assert result["windows"][0]["panes"][0]["title"] == "editor"
    assert "title" not in result["windows"][0]["panes"][1]


def test_expand_pane_titles_disabled() -> None:
    """Test that expand() removes pane title keys when disabled."""
    workspace = {
        "session_name": "test",
        "enable_pane_titles": False,
        "pane_title_position": "top",
        "windows": [
            {
                "window_name": "w1",
                "panes": [{"shell_command": ["echo hi"]}],
            },
        ],
    }
    result = loader.expand(workspace)

    assert "enable_pane_titles" not in result
    assert "pane_title_position" not in result
    assert "options" not in result["windows"][0] or "pane-border-status" not in result[
        "windows"
    ][0].get("options", {})


def test_expand_pane_titles_defaults() -> None:
    """Test that expand() uses default position and format when not specified."""
    workspace = {
        "session_name": "test",
        "enable_pane_titles": True,
        "windows": [
            {
                "window_name": "w1",
                "panes": [{"shell_command": ["echo hi"]}],
            },
        ],
    }
    result = loader.expand(workspace)

    assert result["windows"][0]["options"]["pane-border-status"] == "top"
    assert (
        result["windows"][0]["options"]["pane-border-format"]
        == "#{pane_index}: #{pane_title}"
    )


class PaneTitlePositionFixture(t.NamedTuple):
    """Fixture for pane_title_position validation."""

    test_id: str
    position: str
    expected_position: str
    expect_warning: bool


PANE_TITLE_POSITION_FIXTURES: list[PaneTitlePositionFixture] = [
    PaneTitlePositionFixture(
        test_id="top",
        position="top",
        expected_position="top",
        expect_warning=False,
    ),
    PaneTitlePositionFixture(
        test_id="bottom",
        position="bottom",
        expected_position="bottom",
        expect_warning=False,
    ),
    PaneTitlePositionFixture(
        test_id="off",
        position="off",
        expected_position="off",
        expect_warning=False,
    ),
    PaneTitlePositionFixture(
        test_id="invalid-falls-back-to-top",
        position="invalid_value",
        expected_position="top",
        expect_warning=True,
    ),
]


@pytest.mark.parametrize(
    list(PaneTitlePositionFixture._fields),
    PANE_TITLE_POSITION_FIXTURES,
    ids=[f.test_id for f in PANE_TITLE_POSITION_FIXTURES],
)
def test_expand_pane_title_position_validation(
    caplog: pytest.LogCaptureFixture,
    test_id: str,
    position: str,
    expected_position: str,
    expect_warning: bool,
) -> None:
    """Invalid pane_title_position values default to 'top' with a warning."""
    workspace: dict[str, t.Any] = {
        "session_name": "pos-test",
        "enable_pane_titles": True,
        "pane_title_position": position,
        "windows": [{"window_name": "main", "panes": [{"shell_command": "echo hi"}]}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.loader"):
        result = loader.expand(workspace)

    assert result["windows"][0]["options"]["pane-border-status"] == expected_position

    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    if expect_warning:
        assert any("pane_title_position" in r.message for r in warning_records)
    else:
        assert not any("pane_title_position" in r.message for r in warning_records)


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


def test_expand_lifecycle_hooks_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """expand() expands shell variables in lifecycle hook string values."""
    monkeypatch.setenv("MY_HOOK_CMD", "docker compose up")

    workspace: dict[str, t.Any] = {
        "session_name": "test",
        "on_project_start": "$MY_HOOK_CMD",
        "on_project_stop": "$MY_HOOK_CMD down",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    result = loader.expand(workspace)

    assert result["on_project_start"] == "docker compose up"
    assert result["on_project_stop"] == "docker compose up down"


def test_expand_lifecycle_hooks_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """expand() expands shell variables in lifecycle hook list values."""
    monkeypatch.setenv("MY_CMD", "echo hello")

    workspace: dict[str, t.Any] = {
        "session_name": "test",
        "on_project_start": ["$MY_CMD", "echo world"],
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    result = loader.expand(workspace)

    assert result["on_project_start"] == ["echo hello", "echo world"]


def test_expand_lifecycle_hooks_tilde() -> None:
    """expand() expands ~ in lifecycle hook values."""
    workspace: dict[str, t.Any] = {
        "session_name": "test",
        "on_project_exit": "~/scripts/cleanup.sh",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    result = loader.expand(workspace)

    assert "~" not in result["on_project_exit"]
    assert result["on_project_exit"].endswith("/scripts/cleanup.sh")


class RenderTemplateFixture(t.NamedTuple):
    """Test fixture for render_template tests."""

    test_id: str
    content: str
    context: dict[str, str]
    expected: str


RENDER_TEMPLATE_FIXTURES: list[RenderTemplateFixture] = [
    RenderTemplateFixture(
        test_id="simple-replacement",
        content="root: {{ project }}",
        context={"project": "myapp"},
        expected="root: myapp",
    ),
    RenderTemplateFixture(
        test_id="multiple-vars",
        content="name: {{ name }}\nroot: {{ root }}",
        context={"name": "dev", "root": "/tmp/dev"},
        expected="name: dev\nroot: /tmp/dev",
    ),
    RenderTemplateFixture(
        test_id="unknown-var-unchanged",
        content="root: {{ unknown }}",
        context={"project": "myapp"},
        expected="root: {{ unknown }}",
    ),
    RenderTemplateFixture(
        test_id="no-templates",
        content="root: /tmp/myapp",
        context={"project": "myapp"},
        expected="root: /tmp/myapp",
    ),
    RenderTemplateFixture(
        test_id="env-var-not-affected",
        content="root: $HOME/{{ project }}",
        context={"project": "myapp"},
        expected="root: $HOME/myapp",
    ),
    RenderTemplateFixture(
        test_id="whitespace-in-braces",
        content="root: {{project}}",
        context={"project": "myapp"},
        expected="root: myapp",
    ),
    RenderTemplateFixture(
        test_id="extra-whitespace-in-braces",
        content="root: {{  project  }}",
        context={"project": "myapp"},
        expected="root: myapp",
    ),
    RenderTemplateFixture(
        test_id="empty-context",
        content="root: {{ project }}",
        context={},
        expected="root: {{ project }}",
    ),
    RenderTemplateFixture(
        test_id="same-var-multiple-times",
        content="a: {{ x }}\nb: {{ x }}",
        context={"x": "val"},
        expected="a: val\nb: val",
    ),
]


@pytest.mark.parametrize(
    list(RenderTemplateFixture._fields),
    RENDER_TEMPLATE_FIXTURES,
    ids=[f.test_id for f in RENDER_TEMPLATE_FIXTURES],
)
def test_render_template(
    test_id: str,
    content: str,
    context: dict[str, str],
    expected: str,
) -> None:
    """render_template() replaces {{ var }} expressions with context values."""
    result = loader.render_template(content, context)
    assert result == expected


def test_render_template_rejects_yaml_unsafe_values() -> None:
    """render_template() raises ValueError for YAML-unsafe --set values."""
    with pytest.raises(ValueError, match="YAML-unsafe"):
        loader.render_template("cmd: {{ val }}", {"val": "foo: bar"})

    with pytest.raises(ValueError, match="YAML-unsafe"):
        loader.render_template("cmd: {{ val }}", {"val": "line1\nline2"})

    # Safe values should work fine
    result = loader.render_template("cmd: {{ val }}", {"val": "hello-world"})
    assert result == "cmd: hello-world"
