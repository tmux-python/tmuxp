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
        test_id="multi_flag_config",
        tmuxinator_yaml=fixtures.test4.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test4.tmuxinator_dict,
        tmuxp_dict=fixtures.test4.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="startup_focus_config",
        tmuxinator_yaml=fixtures.test5.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test5.tmuxinator_dict,
        tmuxp_dict=fixtures.test5.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="synchronize_config",
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


class TmuxinatorNamedPaneFixture(t.NamedTuple):
    """Test fixture for tmuxinator named pane conversion."""

    test_id: str
    panes_input: list[t.Any]
    expected_panes: list[t.Any]


TMUXINATOR_NAMED_PANE_FIXTURES: list[TmuxinatorNamedPaneFixture] = [
    TmuxinatorNamedPaneFixture(
        test_id="single-named-pane",
        panes_input=[{"git_log": "git log --oneline"}],
        expected_panes=[
            {"shell_command": ["git log --oneline"], "title": "git_log"},
        ],
    ),
    TmuxinatorNamedPaneFixture(
        test_id="named-pane-list-commands",
        panes_input=[{"server": ["ssh server", "echo hello"]}],
        expected_panes=[
            {"shell_command": ["ssh server", "echo hello"], "title": "server"},
        ],
    ),
    TmuxinatorNamedPaneFixture(
        test_id="plain-panes-unchanged",
        panes_input=["vim", None, "top"],
        expected_panes=["vim", None, "top"],
    ),
]


@pytest.mark.parametrize(
    list(TmuxinatorNamedPaneFixture._fields),
    TMUXINATOR_NAMED_PANE_FIXTURES,
    ids=[test.test_id for test in TMUXINATOR_NAMED_PANE_FIXTURES],
)
def test_convert_named_panes(
    test_id: str,
    panes_input: list[t.Any],
    expected_panes: list[t.Any],
) -> None:
    """Named tmuxinator panes convert to tmuxp pane titles."""
    assert importers._convert_named_panes(panes_input) == expected_panes


def test_import_tmuxinator_named_pane_in_window() -> None:
    """Named pane dictionaries inside window configs are converted."""
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

    assert result["windows"][0]["panes"] == [
        "vim",
        {"shell_command": ["tail -f log/dev.log"], "title": "logs"},
    ]


def test_import_tmuxinator_startup_pane_focuses_default_window() -> None:
    """startup_pane alone focuses the default startup window."""
    workspace = {
        "name": "startup-pane",
        "startup_pane": 0,
        "windows": [
            {"editor": ["vim", "top"]},
            {"server": "rails s"},
        ],
    }

    result = importers.import_tmuxinator(workspace)

    assert result["windows"][0]["focus"] is True
    assert result["windows"][0]["panes"][0] == {
        "shell_command": ["vim"],
        "focus": True,
    }
    assert "focus" not in result["windows"][1]


class TmuxinatorPreWindowFixture(t.NamedTuple):
    """Test fixture for tmuxinator pre-window mapping."""

    test_id: str
    config_extra: dict[str, t.Any]
    expected_shell_command_before: list[str] | None
    expected_on_project_start: str | None


TMUXINATOR_PRE_WINDOW_FIXTURES: list[TmuxinatorPreWindowFixture] = [
    TmuxinatorPreWindowFixture(
        test_id="pre-window-only",
        config_extra={"pre_window": "echo PRE"},
        expected_shell_command_before=["echo PRE"],
        expected_on_project_start=None,
    ),
    TmuxinatorPreWindowFixture(
        test_id="pre-list",
        config_extra={"pre": ["echo one", "echo two"]},
        expected_shell_command_before=None,
        expected_on_project_start="echo one; echo two",
    ),
    TmuxinatorPreWindowFixture(
        test_id="pre-and-pre-window",
        config_extra={"pre": "sudo start", "pre_window": ["cd /app", "nvm use"]},
        expected_shell_command_before=["cd /app; nvm use"],
        expected_on_project_start="sudo start",
    ),
    TmuxinatorPreWindowFixture(
        test_id="rbenv-precedence",
        config_extra={"rbenv": "3.2.0", "pre_window": "echo PRE"},
        expected_shell_command_before=["rbenv shell 3.2.0"],
        expected_on_project_start=None,
    ),
    TmuxinatorPreWindowFixture(
        test_id="rvm-precedence",
        config_extra={"rvm": "2.1.1", "pre_tab": "source .env"},
        expected_shell_command_before=["rvm use 2.1.1"],
        expected_on_project_start=None,
    ),
]


@pytest.mark.parametrize(
    list(TmuxinatorPreWindowFixture._fields),
    TMUXINATOR_PRE_WINDOW_FIXTURES,
    ids=[test.test_id for test in TMUXINATOR_PRE_WINDOW_FIXTURES],
)
def test_import_tmuxinator_pre_window_mapping(
    test_id: str,
    config_extra: dict[str, t.Any],
    expected_shell_command_before: list[str] | None,
    expected_on_project_start: str | None,
) -> None:
    """Pre maps to project start; pre-window keys map to shell_command_before."""
    workspace: dict[str, t.Any] = {
        "name": "pre-test",
        "windows": [{"editor": "vim"}],
        **config_extra,
    }

    result = importers.import_tmuxinator(workspace)

    if expected_shell_command_before is None:
        assert "shell_command_before" not in result
    else:
        assert result["shell_command_before"] == expected_shell_command_before

    if expected_on_project_start is None:
        assert "on_project_start" not in result
    else:
        assert result["on_project_start"] == expected_on_project_start


def test_import_tmuxinator_socket_name_conflict_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Explicit socket_name warns when it overrides cli_args -L."""
    workspace = {
        "name": "conflict",
        "cli_args": "-L from_cli",
        "socket_name": "explicit",
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        result = importers.import_tmuxinator(workspace)

    assert result["socket_name"] == "explicit"
    assert any("explicit" in record.message for record in caplog.records)
    assert any("from_cli" in record.message for record in caplog.records)


def test_import_tmuxinator_attached_tmux_flags() -> None:
    """Attached tmux flags like -Lsocket are parsed."""
    workspace = {
        "name": "attached-flags",
        "cli_args": "-f./tmux.conf -Lmysocket -S/tmp/tmux.sock",
        "windows": [{"editor": "vim"}],
    }

    result = importers.import_tmuxinator(workspace)

    assert result["config"] == "./tmux.conf"
    assert result["socket_name"] == "mysocket"
    assert result["socket_path"] == "/tmp/tmux.sock"


def test_import_tmuxinator_passthrough_pane_titles_and_hooks() -> None:
    """Native tmuxp pane title and lifecycle hook keys pass through."""
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


def test_import_tmuxinator_numeric_window_names_expand() -> None:
    """Numeric YAML window keys become strings before loader expansion."""
    from tmuxp.workspace import loader

    workspace = {
        "name": "test",
        "windows": [{222: "echo hello"}, {True: "echo bool"}],
    }

    result = importers.import_tmuxinator(workspace)
    expanded = loader.expand(result)

    assert expanded["windows"][0]["window_name"] == "222"
    assert expanded["windows"][1]["window_name"] == "True"
