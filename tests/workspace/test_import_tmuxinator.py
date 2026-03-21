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


def test_logs_info_on_multi_command_pre_list(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that multi-command pre list logs info about before_script mapping."""
    workspace = {
        "name": "multi-pre",
        "root": "~/test",
        "pre": ["cmd1", "cmd2"],
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.INFO, logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(workspace)

    pre_records = [r for r in caplog.records if "multi-command pre list" in r.message]
    assert len(pre_records) == 1


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


def test_import_tmuxinator_pre_list_joined_for_before_script() -> None:
    """List pre values are joined with '; ' so expand() doesn't crash."""
    workspace = {
        "name": "pre-list",
        "windows": [{"editor": "vim"}],
        "pre": ["echo one", "echo two"],
    }
    result = importers.import_tmuxinator(workspace)
    assert result["before_script"] == "echo one; echo two"

    # Verify it survives expand() without TypeError
    from tmuxp.workspace import loader

    loader.expand(result)


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

    assert result["on_project_first_start"] == "rake db:create"
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("on_project_first_start" in r.message for r in warning_records)
