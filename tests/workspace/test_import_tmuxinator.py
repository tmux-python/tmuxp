"""Test for tmuxp tmuxinator configuration."""

from __future__ import annotations

import logging
import typing as t

import pytest

from tests.fixtures import import_tmuxinator as fixtures
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.workspace import importers, validation


class TmuxinatorConfigTestFixture(t.NamedTuple):
    """Test fixture for tmuxinator config conversion tests."""

    test_id: str
    tmuxinator_yaml: str
    tmuxinator_dict: dict[str, t.Any]
    tmuxp_dict: dict[str, t.Any]


TMUXINATOR_CONFIG_TEST_FIXTURES: list[TmuxinatorConfigTestFixture] = [
    TmuxinatorConfigTestFixture(
        test_id="basic_config",
        tmuxinator_yaml=fixtures.test1.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test1.tmuxinator_dict,
        tmuxp_dict=fixtures.test1.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="legacy_tabs_config",  # older vers use `tabs` instead of `windows`
        tmuxinator_yaml=fixtures.test2.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test2.tmuxinator_dict,
        tmuxp_dict=fixtures.test2.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="sample_config",  # Test importing <spec/fixtures/sample.yml>
        tmuxinator_yaml=fixtures.test3.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test3.tmuxinator_dict,
        tmuxp_dict=fixtures.test3.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="multi_flag_cli_args",
        tmuxinator_yaml=fixtures.test4.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test4.tmuxinator_dict,
        tmuxp_dict=fixtures.test4.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="rvm_pre_tab_startup",
        tmuxinator_yaml=fixtures.test5.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test5.tmuxinator_dict,
        tmuxp_dict=fixtures.test5.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="synchronize",
        tmuxinator_yaml=fixtures.test6.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test6.tmuxinator_dict,
        tmuxp_dict=fixtures.test6.expected,
    ),
]


@pytest.mark.parametrize(
    list(TmuxinatorConfigTestFixture._fields),
    TMUXINATOR_CONFIG_TEST_FIXTURES,
    ids=[test.test_id for test in TMUXINATOR_CONFIG_TEST_FIXTURES],
)
def test_config_to_dict(
    test_id: str,
    tmuxinator_yaml: str,
    tmuxinator_dict: dict[str, t.Any],
    tmuxp_dict: dict[str, t.Any],
) -> None:
    """Test exporting tmuxinator configuration to dictionary."""
    yaml_to_dict = ConfigReader._load(fmt="yaml", content=tmuxinator_yaml)
    assert yaml_to_dict == tmuxinator_dict

    assert importers.import_tmuxinator(tmuxinator_dict) == tmuxp_dict

    validation.validate_schema(importers.import_tmuxinator(tmuxinator_dict))


def test_import_tmuxinator_logs_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """import_tmuxinator() logs DEBUG record."""
    workspace = {
        "name": "test",
        "windows": [{"main": ["echo hi"]}],
    }
    with caplog.at_level(logging.DEBUG, logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(workspace)
    records = [r for r in caplog.records if r.msg == "importing tmuxinator workspace"]
    assert len(records) >= 1
    assert getattr(records[0], "tmux_session", None) == "test"


def test_startup_window_sets_focus_by_name() -> None:
    """Startup_window sets focus on the matching window by name."""
    workspace = {
        "name": "test",
        "startup_window": "logs",
        "windows": [
            {"editor": "vim"},
            {"logs": "tail -f log/dev.log"},
        ],
    }
    result = importers.import_tmuxinator(workspace)

    assert result["windows"][0].get("focus") is None
    assert result["windows"][1]["focus"] is True


def test_startup_window_sets_focus_by_index() -> None:
    """Startup_window sets focus by numeric index when name doesn't match."""
    workspace = {
        "name": "test",
        "startup_window": 1,
        "windows": [
            {"editor": "vim"},
            {"server": "rails s"},
        ],
    }
    result = importers.import_tmuxinator(workspace)

    assert result["windows"][0].get("focus") is None
    assert result["windows"][1]["focus"] is True


def test_startup_pane_sets_focus_on_pane() -> None:
    """Startup_pane converts the target pane to a dict with focus."""
    workspace = {
        "name": "test",
        "startup_window": "editor",
        "startup_pane": 1,
        "windows": [
            {
                "editor": {
                    "panes": ["vim", "guard", "top"],
                },
            },
        ],
    }
    result = importers.import_tmuxinator(workspace)

    assert result["windows"][0]["focus"] is True
    panes = result["windows"][0]["panes"]
    assert panes[0] == "vim"
    assert panes[1] == {"shell_command": ["guard"], "focus": True}
    assert panes[2] == "top"


def test_startup_pane_without_startup_window() -> None:
    """Startup_pane targets the first window when no startup_window is set."""
    workspace = {
        "name": "test",
        "startup_pane": 1,
        "windows": [
            {
                "editor": {
                    "panes": ["vim", "guard"],
                },
            },
        ],
    }
    result = importers.import_tmuxinator(workspace)

    panes = result["windows"][0]["panes"]
    assert panes[1] == {"shell_command": ["guard"], "focus": True}


def test_startup_window_warns_on_no_match(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Startup_window logs WARNING when no matching window is found."""
    workspace = {
        "name": "test",
        "startup_window": "nonexistent",
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(workspace)

    warn_records = [r for r in caplog.records if "startup_window" in r.message]
    assert len(warn_records) == 1


class YamlEdgeCaseFixture(t.NamedTuple):
    """Test fixture for YAML edge case tests."""

    test_id: str
    workspace: dict[str, t.Any]
    expected_window_names: list[str | None]


YAML_EDGE_CASE_FIXTURES: list[YamlEdgeCaseFixture] = [
    YamlEdgeCaseFixture(
        test_id="numeric-window-name",
        workspace={
            "name": "test",
            "windows": [{222: "echo hello"}],
        },
        expected_window_names=["222"],
    ),
    YamlEdgeCaseFixture(
        test_id="boolean-true-window-name",
        workspace={
            "name": "test",
            "windows": [{True: "echo true"}],
        },
        expected_window_names=["True"],
    ),
    YamlEdgeCaseFixture(
        test_id="boolean-false-window-name",
        workspace={
            "name": "test",
            "windows": [{False: "echo false"}],
        },
        expected_window_names=["False"],
    ),
    YamlEdgeCaseFixture(
        test_id="float-window-name",
        workspace={
            "name": "test",
            "windows": [{222.3: "echo float"}],
        },
        expected_window_names=["222.3"],
    ),
    YamlEdgeCaseFixture(
        test_id="none-window-name",
        workspace={
            "name": "test",
            "windows": [{None: "echo none"}],
        },
        expected_window_names=[None],
    ),
    YamlEdgeCaseFixture(
        test_id="emoji-window-name",
        workspace={
            "name": "test",
            "windows": [{"🍩": "echo donut"}],
        },
        expected_window_names=["🍩"],
    ),
    YamlEdgeCaseFixture(
        test_id="mixed-type-window-names",
        workspace={
            "name": "test",
            "windows": [
                {222: "echo int"},
                {True: "echo bool"},
                {"normal": "echo str"},
            ],
        },
        expected_window_names=["222", "True", "normal"],
    ),
]


@pytest.mark.parametrize(
    list(YamlEdgeCaseFixture._fields),
    YAML_EDGE_CASE_FIXTURES,
    ids=[f.test_id for f in YAML_EDGE_CASE_FIXTURES],
)
def test_import_tmuxinator_window_name_coercion(
    workspace: dict[str, t.Any],
    expected_window_names: list[str | None],
    test_id: str,
) -> None:
    """Window names are coerced to strings for YAML type-coerced keys."""
    result = importers.import_tmuxinator(workspace)
    actual_names = [w["window_name"] for w in result["windows"]]
    assert actual_names == expected_window_names


def test_import_tmuxinator_numeric_window_survives_expand() -> None:
    """Numeric window names don't crash expand() after str coercion."""
    from tmuxp.workspace import loader

    workspace = {
        "name": "test",
        "windows": [{222: "echo hello"}, {True: "echo bool"}],
    }
    result = importers.import_tmuxinator(workspace)
    expanded = loader.expand(result)

    assert expanded["windows"][0]["window_name"] == "222"
    assert expanded["windows"][1]["window_name"] == "True"


def test_import_tmuxinator_yaml_aliases() -> None:
    """YAML aliases/anchors resolve transparently before import."""
    yaml_content = """\
defaults: &defaults
  pre:
    - echo "alias_is_working"

name: sample_alias
root: ~/test
windows:
  - editor:
      <<: *defaults
      layout: main-vertical
      panes:
        - vim
        - top
  - guard:
"""
    parsed = ConfigReader._load(fmt="yaml", content=yaml_content)
    result = importers.import_tmuxinator(parsed)

    assert result["session_name"] == "sample_alias"
    assert result["windows"][0]["window_name"] == "editor"
    assert result["windows"][0]["shell_command_before"] == [
        'echo "alias_is_working"',
    ]
    assert result["windows"][0]["layout"] == "main-vertical"
    assert result["windows"][0]["panes"] == ["vim", "top"]
    assert result["windows"][1]["window_name"] == "guard"


class NamedPaneFixture(t.NamedTuple):
    """Test fixture for named pane conversion tests."""

    test_id: str
    panes_input: list[t.Any]
    expected_panes: list[t.Any]


NAMED_PANE_FIXTURES: list[NamedPaneFixture] = [
    NamedPaneFixture(
        test_id="single-named-pane",
        panes_input=[{"git_log": "git log --oneline"}],
        expected_panes=[
            {"shell_command": ["git log --oneline"], "title": "git_log"},
        ],
    ),
    NamedPaneFixture(
        test_id="named-pane-with-list-commands",
        panes_input=[{"server": ["ssh server", "echo hello"]}],
        expected_panes=[
            {"shell_command": ["ssh server", "echo hello"], "title": "server"},
        ],
    ),
    NamedPaneFixture(
        test_id="mixed-named-and-plain-panes",
        panes_input=["vim", {"logs": ["tail -f log"]}, "top"],
        expected_panes=[
            "vim",
            {"shell_command": ["tail -f log"], "title": "logs"},
            "top",
        ],
    ),
    NamedPaneFixture(
        test_id="named-pane-with-none-command",
        panes_input=[{"empty": None}],
        expected_panes=[
            {"shell_command": [], "title": "empty"},
        ],
    ),
    NamedPaneFixture(
        test_id="no-named-panes",
        panes_input=["vim", None, "top"],
        expected_panes=["vim", None, "top"],
    ),
]


@pytest.mark.parametrize(
    list(NamedPaneFixture._fields),
    NAMED_PANE_FIXTURES,
    ids=[f.test_id for f in NAMED_PANE_FIXTURES],
)
def test_convert_named_panes(
    test_id: str,
    panes_input: list[t.Any],
    expected_panes: list[t.Any],
) -> None:
    """_convert_named_panes() converts {name: commands} dicts to title+shell_command."""
    result = importers._convert_named_panes(panes_input)
    assert result == expected_panes


def test_import_tmuxinator_named_pane_in_window() -> None:
    """Named pane dicts inside window config are converted with title."""
    workspace = {
        "name": "test",
        "windows": [
            {
                "editor": {
                    "panes": [
                        "vim",
                        {"logs": ["tail -f log/dev.log"]},
                    ],
                },
            },
        ],
    }
    result = importers.import_tmuxinator(workspace)
    panes = result["windows"][0]["panes"]
    assert panes[0] == "vim"
    assert panes[1] == {"shell_command": ["tail -f log/dev.log"], "title": "logs"}


def test_import_tmuxinator_named_pane_in_list_window() -> None:
    """Named pane dicts in list-form windows are converted with title."""
    workspace = {
        "name": "test",
        "windows": [
            {"editor": ["vim", {"server": "rails s"}, "top"]},
        ],
    }
    result = importers.import_tmuxinator(workspace)
    panes = result["windows"][0]["panes"]
    assert panes[0] == "vim"
    assert panes[1] == {"shell_command": ["rails s"], "title": "server"}
    assert panes[2] == "top"


def test_import_tmuxinator_socket_name_conflict_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Warn when explicit socket_name overrides -L from cli_args."""
    workspace = {
        "name": "conflict",
        "cli_args": "-L from_cli",
        "socket_name": "explicit",
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        result = importers.import_tmuxinator(workspace)

    assert result["socket_name"] == "explicit"
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warning_records) == 1
    assert "explicit" in warning_records[0].message
    assert "from_cli" in warning_records[0].message


def test_import_tmuxinator_socket_name_same_no_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """No warning when cli_args -L and explicit socket_name match."""
    workspace = {
        "name": "same",
        "cli_args": "-L same_socket",
        "socket_name": "same_socket",
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        result = importers.import_tmuxinator(workspace)

    assert result["socket_name"] == "same_socket"
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warning_records) == 0


def test_import_tmuxinator_pre_list_joined_for_on_project_start() -> None:
    """List pre values are joined with '; ' for on_project_start."""
    workspace = {
        "name": "pre-list",
        "windows": [{"editor": "vim"}],
        "pre": ["echo one", "echo two"],
    }
    result = importers.import_tmuxinator(workspace)
    assert result["on_project_start"] == "echo one; echo two"

    # Verify it survives expand() without TypeError
    from tmuxp.workspace import loader

    loader.expand(result)


class PreVsPassthroughFixture(t.NamedTuple):
    """Test fixture for pre vs on_project_start passthrough precedence."""

    test_id: str
    workspace: dict[str, t.Any]
    expected_on_project_start: str


PRE_VS_PASSTHROUGH_FIXTURES: list[PreVsPassthroughFixture] = [
    PreVsPassthroughFixture(
        test_id="passthrough_wins_over_pre",
        workspace={
            "name": "both-keys",
            "on_project_start": "echo native-start",
            "pre": "echo legacy-pre",
            "windows": [{"editor": "vim"}],
        },
        expected_on_project_start="echo native-start",
    ),
    PreVsPassthroughFixture(
        test_id="pre_maps_when_no_passthrough",
        workspace={
            "name": "pre-only",
            "pre": "echo starting",
            "windows": [{"editor": "vim"}],
        },
        expected_on_project_start="echo starting",
    ),
]


@pytest.mark.parametrize(
    list(PreVsPassthroughFixture._fields),
    PRE_VS_PASSTHROUGH_FIXTURES,
    ids=[f.test_id for f in PRE_VS_PASSTHROUGH_FIXTURES],
)
def test_import_tmuxinator_pre_vs_passthrough_on_project_start(
    test_id: str,
    workspace: dict[str, t.Any],
    expected_on_project_start: str,
) -> None:
    """Passthrough on_project_start takes precedence over legacy pre key."""
    result = importers.import_tmuxinator(workspace)
    assert result["on_project_start"] == expected_on_project_start


def test_import_tmuxinator_passthrough_pane_titles_and_hooks() -> None:
    """Pane title and lifecycle hook keys are copied through to tmuxp config."""
    workspace = {
        "name": "passthrough",
        "enable_pane_titles": True,
        "pane_title_position": "bottom",
        "pane_title_format": "#{pane_index}",
        "on_project_start": "echo starting",
        "on_project_restart": "echo restarting",
        "on_project_exit": "echo exiting",
        "on_project_stop": "echo stopping",
        "windows": [{"editor": "vim"}],
    }
    result = importers.import_tmuxinator(workspace)

    assert result["enable_pane_titles"] is True
    assert result["pane_title_position"] == "bottom"
    assert result["pane_title_format"] == "#{pane_index}"
    assert result["on_project_start"] == "echo starting"
    assert result["on_project_restart"] == "echo restarting"
    assert result["on_project_exit"] == "echo exiting"
    assert result["on_project_stop"] == "echo stopping"


def test_import_tmuxinator_on_project_first_start_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Warn when on_project_first_start is used (not yet supported by tmuxp)."""
    workspace = {
        "name": "first-start",
        "on_project_first_start": "rake db:create",
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        result = importers.import_tmuxinator(workspace)

    assert "on_project_first_start" not in result
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("on_project_first_start" in r.message for r in warning_records)


class UnmappedKeyFixture(t.NamedTuple):
    """Fixture for tmuxinator keys with no tmuxp equivalent."""

    test_id: str
    key: str
    value: t.Any


UNMAPPED_KEY_FIXTURES: list[UnmappedKeyFixture] = [
    UnmappedKeyFixture(
        test_id="tmux_command",
        key="tmux_command",
        value="wemux",
    ),
    UnmappedKeyFixture(
        test_id="attach",
        key="attach",
        value=False,
    ),
    UnmappedKeyFixture(
        test_id="post",
        key="post",
        value="echo done",
    ),
]


@pytest.mark.parametrize(
    list(UnmappedKeyFixture._fields),
    UNMAPPED_KEY_FIXTURES,
    ids=[f.test_id for f in UNMAPPED_KEY_FIXTURES],
)
def test_import_tmuxinator_warns_on_unmapped_key(
    caplog: pytest.LogCaptureFixture,
    test_id: str,
    key: str,
    value: t.Any,
) -> None:
    """Unmapped tmuxinator keys log a warning instead of being silently dropped."""
    workspace = {
        "name": "unmapped-test",
        "windows": [{"editor": "vim"}],
        key: value,
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(workspace)

    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any(key in r.message for r in warning_records)


class PreWindowStandaloneFixture(t.NamedTuple):
    """Fixture for pre_window/pre_tab without pre key."""

    test_id: str
    config_extra: dict[str, t.Any]
    expect_shell_command_before: list[str] | None
    expect_on_project_start: str | None


PRE_WINDOW_STANDALONE_FIXTURES: list[PreWindowStandaloneFixture] = [
    PreWindowStandaloneFixture(
        test_id="pre_window-only",
        config_extra={"pre_window": "echo PRE"},
        expect_shell_command_before=["echo PRE"],
        expect_on_project_start=None,
    ),
    PreWindowStandaloneFixture(
        test_id="pre_tab-only",
        config_extra={"pre_tab": "rbenv shell 3.0"},
        expect_shell_command_before=["rbenv shell 3.0"],
        expect_on_project_start=None,
    ),
    PreWindowStandaloneFixture(
        test_id="pre_window-list",
        config_extra={"pre_window": ["echo a", "echo b"]},
        expect_shell_command_before=["echo a; echo b"],
        expect_on_project_start=None,
    ),
    PreWindowStandaloneFixture(
        test_id="pre-and-pre_window",
        config_extra={"pre": "sudo start", "pre_window": "echo PRE"},
        expect_shell_command_before=["echo PRE"],
        expect_on_project_start="sudo start",
    ),
    PreWindowStandaloneFixture(
        test_id="pre-and-pre_window-list",
        config_extra={"pre": "sudo start", "pre_window": ["cd /app", "nvm use 18"]},
        expect_shell_command_before=["cd /app; nvm use 18"],
        expect_on_project_start="sudo start",
    ),
    PreWindowStandaloneFixture(
        test_id="pre-only",
        config_extra={"pre": "sudo start"},
        expect_shell_command_before=None,
        expect_on_project_start="sudo start",
    ),
]


@pytest.mark.parametrize(
    list(PreWindowStandaloneFixture._fields),
    PRE_WINDOW_STANDALONE_FIXTURES,
    ids=[f.test_id for f in PRE_WINDOW_STANDALONE_FIXTURES],
)
def test_import_tmuxinator_pre_window_standalone(
    test_id: str,
    config_extra: dict[str, t.Any],
    expect_shell_command_before: list[str] | None,
    expect_on_project_start: str | None,
) -> None:
    """pre_window/pre_tab map to shell_command_before independently of pre."""
    workspace: dict[str, t.Any] = {
        "name": "pre-window-test",
        "windows": [{"editor": "vim"}],
        **config_extra,
    }
    result = importers.import_tmuxinator(workspace)

    if expect_shell_command_before is not None:
        assert result.get("shell_command_before") == expect_shell_command_before
    else:
        assert "shell_command_before" not in result

    if expect_on_project_start is not None:
        assert result.get("on_project_start") == expect_on_project_start
    else:
        assert "on_project_start" not in result


class PreWindowPrecedenceFixture(t.NamedTuple):
    """Fixture for rbenv/rvm/pre_tab/pre_window exclusive precedence."""

    test_id: str
    config_extra: dict[str, t.Any]
    expect_shell_command_before: list[str]


PRE_WINDOW_PRECEDENCE_FIXTURES: list[PreWindowPrecedenceFixture] = [
    PreWindowPrecedenceFixture(
        test_id="rbenv-beats-pre_window",
        config_extra={"rbenv": "2.7.0", "pre_window": "echo PRE"},
        expect_shell_command_before=["rbenv shell 2.7.0"],
    ),
    PreWindowPrecedenceFixture(
        test_id="rvm-beats-pre_tab",
        config_extra={"rvm": "2.1.1", "pre_tab": "source .env"},
        expect_shell_command_before=["rvm use 2.1.1"],
    ),
    PreWindowPrecedenceFixture(
        test_id="rbenv-beats-rvm",
        config_extra={"rbenv": "3.2.0", "rvm": "2.1.1"},
        expect_shell_command_before=["rbenv shell 3.2.0"],
    ),
    PreWindowPrecedenceFixture(
        test_id="pre_tab-beats-pre_window",
        config_extra={"pre_tab": "nvm use 18", "pre_window": "echo OTHER"},
        expect_shell_command_before=["nvm use 18"],
    ),
]


@pytest.mark.parametrize(
    list(PreWindowPrecedenceFixture._fields),
    PRE_WINDOW_PRECEDENCE_FIXTURES,
    ids=[f.test_id for f in PRE_WINDOW_PRECEDENCE_FIXTURES],
)
def test_import_tmuxinator_pre_window_precedence(
    test_id: str,
    config_extra: dict[str, t.Any],
    expect_shell_command_before: list[str],
) -> None:
    """Tmuxinator uses exclusive rbenv > rvm > pre_tab > pre_window precedence."""
    workspace: dict[str, t.Any] = {
        "name": "precedence-test",
        "windows": [{"editor": "vim"}],
        **config_extra,
    }
    result = importers.import_tmuxinator(workspace)
    assert result.get("shell_command_before") == expect_shell_command_before


class StartupIndexFixture(t.NamedTuple):
    """Fixture for startup_window/startup_pane numeric index resolution."""

    test_id: str
    startup_window: str | int
    window_names: list[str]
    expected_focus_index: int | None
    expect_info_log: bool
    expect_warning_log: bool


STARTUP_INDEX_FIXTURES: list[StartupIndexFixture] = [
    StartupIndexFixture(
        test_id="name-match",
        startup_window="editor",
        window_names=["editor", "console"],
        expected_focus_index=0,
        expect_info_log=False,
        expect_warning_log=False,
    ),
    StartupIndexFixture(
        test_id="numeric-zero",
        startup_window=0,
        window_names=["win1", "win2"],
        expected_focus_index=0,
        expect_info_log=False,
        expect_warning_log=True,
    ),
    StartupIndexFixture(
        test_id="numeric-one",
        startup_window=1,
        window_names=["win1", "win2"],
        expected_focus_index=1,
        expect_info_log=False,
        expect_warning_log=True,
    ),
    StartupIndexFixture(
        test_id="out-of-range",
        startup_window=5,
        window_names=["win1", "win2"],
        expected_focus_index=None,
        expect_info_log=False,
        expect_warning_log=True,
    ),
    StartupIndexFixture(
        test_id="no-match-string",
        startup_window="nonexistent",
        window_names=["win1", "win2"],
        expected_focus_index=None,
        expect_info_log=False,
        expect_warning_log=True,
    ),
]


@pytest.mark.parametrize(
    list(StartupIndexFixture._fields),
    STARTUP_INDEX_FIXTURES,
    ids=[f.test_id for f in STARTUP_INDEX_FIXTURES],
)
def test_import_tmuxinator_startup_window_index_resolution(
    caplog: pytest.LogCaptureFixture,
    test_id: str,
    startup_window: str | int,
    window_names: list[str],
    expected_focus_index: int | None,
    expect_info_log: bool,
    expect_warning_log: bool,
) -> None:
    """startup_window resolves by name first, then 0-based index with logging."""
    workspace: dict[str, t.Any] = {
        "name": "startup-test",
        "startup_window": startup_window,
        "windows": [{wn: "echo hi"} for wn in window_names],
    }
    with caplog.at_level(logging.DEBUG, logger="tmuxp.workspace.importers"):
        result = importers.import_tmuxinator(workspace)

    windows = result["windows"]
    for i, w in enumerate(windows):
        if expected_focus_index is not None and i == expected_focus_index:
            assert w.get("focus") is True, f"window {i} should have focus"
        else:
            assert not w.get("focus"), f"window {i} should not have focus"

    info_records = [
        r
        for r in caplog.records
        if r.levelno == logging.INFO and "startup_window" in r.message
    ]
    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and "startup_window" in r.message
    ]

    if expect_info_log:
        assert len(info_records) >= 1
    else:
        assert len(info_records) == 0

    if expect_warning_log:
        assert len(warning_records) >= 1
    else:
        assert len(warning_records) == 0


def test_import_tmuxinator_cli_args_attached_flags() -> None:
    """Tmuxinator cli_args with attached POSIX flags like -Lmysocket."""
    workspace = {
        "name": "attached-flags",
        "root": "~/app",
        "cli_args": "-f~/.tmux.mac.conf -Lmysocket",
        "windows": [{"editor": "vim"}],
    }
    result = importers.import_tmuxinator(workspace)

    assert result["config"] == "~/.tmux.mac.conf"
    assert result["socket_name"] == "mysocket"


def test_import_tmuxinator_none_window_name_no_crash() -> None:
    """Tmuxinator config with None (null) window key imports without crashing."""
    workspace = {
        "name": "null-window",
        "windows": [{None: "vim"}],
    }
    result = importers.import_tmuxinator(workspace)

    assert result["windows"][0]["window_name"] is None
    assert result["windows"][0]["panes"] == ["vim"]

    # Verify expand + trickle don't crash on None window_name
    from tmuxp.workspace import loader

    expanded = loader.expand(result)
    loader.trickle(expanded)
