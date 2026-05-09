"""Test for tmuxp teamocil configuration."""

from __future__ import annotations

import logging
import typing as t

import pytest

from tests.fixtures import import_teamocil as fixtures
from tmuxp._internal import config_reader
from tmuxp.workspace import importers, validation


class TeamocilConfigTestFixture(t.NamedTuple):
    """Test fixture for teamocil config conversion tests."""

    test_id: str
    teamocil_yaml: str
    teamocil_dict: dict[str, t.Any]
    tmuxp_dict: dict[str, t.Any]


TEAMOCIL_CONFIG_TEST_FIXTURES: list[TeamocilConfigTestFixture] = [
    TeamocilConfigTestFixture(
        test_id="test1",
        teamocil_yaml=fixtures.test1.teamocil_yaml,
        teamocil_dict=fixtures.test1.teamocil_conf,
        tmuxp_dict=fixtures.test1.expected,
    ),
    TeamocilConfigTestFixture(
        test_id="test2",
        teamocil_yaml=fixtures.test2.teamocil_yaml,
        teamocil_dict=fixtures.test2.teamocil_dict,
        tmuxp_dict=fixtures.test2.expected,
    ),
    TeamocilConfigTestFixture(
        test_id="test3",
        teamocil_yaml=fixtures.test3.teamocil_yaml,
        teamocil_dict=fixtures.test3.teamocil_dict,
        tmuxp_dict=fixtures.test3.expected,
    ),
    TeamocilConfigTestFixture(
        test_id="test4",
        teamocil_yaml=fixtures.test4.teamocil_yaml,
        teamocil_dict=fixtures.test4.teamocil_dict,
        tmuxp_dict=fixtures.test4.expected,
    ),
    TeamocilConfigTestFixture(
        test_id="with_env_var_default",  # v0.x default exports TEAMOCIL=1
        teamocil_yaml=fixtures.test_with_env_var_default.teamocil_yaml,
        teamocil_dict=fixtures.test_with_env_var_default.teamocil_dict,
        tmuxp_dict=fixtures.test_with_env_var_default.expected,
    ),
    TeamocilConfigTestFixture(
        test_id="with_env_var_false",  # explicit false suppresses
        teamocil_yaml=fixtures.test_with_env_var_false.teamocil_yaml,
        teamocil_dict=fixtures.test_with_env_var_false.teamocil_dict,
        tmuxp_dict=fixtures.test_with_env_var_false.expected,
    ),
    TeamocilConfigTestFixture(
        test_id="v1x_string_pane",  # bare string pane -> shell_command list
        teamocil_yaml=fixtures.test_v1x_string_pane.teamocil_yaml,
        teamocil_dict=fixtures.test_v1x_string_pane.teamocil_dict,
        tmuxp_dict=fixtures.test_v1x_string_pane.expected,
    ),
    TeamocilConfigTestFixture(
        test_id="v1x_full",  # commands, focus, options, mixed panes
        teamocil_yaml=fixtures.test_v1x_full.teamocil_yaml,
        teamocil_dict=fixtures.test_v1x_full.teamocil_dict,
        tmuxp_dict=fixtures.test_v1x_full.expected,
    ),
]


@pytest.mark.parametrize(
    list(TeamocilConfigTestFixture._fields),
    TEAMOCIL_CONFIG_TEST_FIXTURES,
    ids=[test.test_id for test in TEAMOCIL_CONFIG_TEST_FIXTURES],
)
def test_config_to_dict(
    test_id: str,
    teamocil_yaml: str,
    teamocil_dict: dict[str, t.Any],
    tmuxp_dict: dict[str, t.Any],
) -> None:
    """Test exporting teamocil configuration to dictionary."""
    yaml_to_dict = config_reader.ConfigReader._load(
        fmt="yaml",
        content=teamocil_yaml,
    )
    assert yaml_to_dict == teamocil_dict

    assert importers.import_teamocil(teamocil_dict) == tmuxp_dict

    validation.validate_schema(importers.import_teamocil(teamocil_dict))


@pytest.fixture(scope="module")
def multisession_config() -> dict[
    str,
    dict[str, t.Any],
]:
    """Return loaded multisession teamocil config as a dictionary.

    Also prevents re-running assertion the loads the yaml, since ordering of
    deep list items like panes will be inconsistent.
    """
    teamocil_yaml_file = fixtures.layouts.teamocil_yaml_file
    test_config = config_reader.ConfigReader._from_file(teamocil_yaml_file)
    teamocil_dict: dict[str, t.Any] = fixtures.layouts.teamocil_dict

    assert test_config == teamocil_dict
    return teamocil_dict


class TeamocilMultiSessionTestFixture(t.NamedTuple):
    """Test fixture for teamocil multisession config tests."""

    test_id: str
    session_name: str
    expected: dict[str, t.Any]


TEAMOCIL_MULTISESSION_TEST_FIXTURES: list[TeamocilMultiSessionTestFixture] = [
    TeamocilMultiSessionTestFixture(
        test_id="basic_two_windows",
        session_name="two-windows",
        expected=fixtures.layouts.two_windows,
    ),
    TeamocilMultiSessionTestFixture(
        test_id="two_windows_with_filters",
        session_name="two-windows-with-filters",
        expected=fixtures.layouts.two_windows_with_filters,
    ),
    TeamocilMultiSessionTestFixture(
        test_id="two_windows_with_custom_command_options",
        session_name="two-windows-with-custom-command-options",
        expected=fixtures.layouts.two_windows_with_custom_command_options,
    ),
    TeamocilMultiSessionTestFixture(
        test_id="three_windows_within_session",
        session_name="three-windows-within-a-session",
        expected=fixtures.layouts.three_windows_within_a_session,
    ),
]


@pytest.mark.parametrize(
    list(TeamocilMultiSessionTestFixture._fields),
    TEAMOCIL_MULTISESSION_TEST_FIXTURES,
    ids=[test.test_id for test in TEAMOCIL_MULTISESSION_TEST_FIXTURES],
)
def test_multisession_config(
    test_id: str,
    session_name: str,
    expected: dict[str, t.Any],
    multisession_config: dict[str, t.Any],
) -> None:
    """Test importing teamocil multisession configuration."""
    # teamocil can fit multiple sessions in a config
    assert importers.import_teamocil(multisession_config[session_name]) == expected

    validation.validate_schema(
        importers.import_teamocil(multisession_config[session_name]),
    )


def test_import_teamocil_logs_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """import_teamocil() logs DEBUG record."""
    workspace = {
        "session": {
            "name": "test",
            "windows": [{"name": "main", "panes": [{"cmd": "echo hi"}]}],
        },
    }
    with caplog.at_level(logging.DEBUG, logger="tmuxp.workspace.importers"):
        importers.import_teamocil(workspace)
    records = [r for r in caplog.records if r.msg == "importing teamocil workspace"]
    assert len(records) >= 1
    assert getattr(records[0], "tmux_session", None) == "test"


def test_import_teamocil_with_env_var_string_false_suppresses() -> None:
    """A YAML-quoted ``with_env_var`` of ``false`` suppresses TEAMOCIL=1."""
    workspace = {
        "session": {
            "name": "string-false",
            "with_env_var": "false",
            "windows": [{"name": "main", "panes": [{"cmd": "echo hi"}]}],
        },
    }
    result = importers.import_teamocil(workspace)
    assert "environment" not in result


def test_import_teamocil_warns_on_cmd_separator(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`cmd_separator` emits WARNING."""
    workspace = {
        "session": {
            "name": "sep",
            "cmd_separator": " && ",
            "windows": [{"name": "main", "panes": [{"cmd": "echo hi"}]}],
        },
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_teamocil(workspace)
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and getattr(r, "tmux_key", None) == "cmd_separator"
    ]
    assert len(warnings) == 1


def test_import_teamocil_warns_on_clear(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`clear` on a window emits WARNING."""
    workspace = {
        "session": {
            "name": "clr",
            "windows": [
                {"name": "main", "clear": True, "panes": [{"cmd": "echo hi"}]},
            ],
        },
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_teamocil(workspace)
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and getattr(r, "tmux_key", None) == "clear"
    ]
    assert len(warnings) == 1


def test_import_teamocil_v1x_skips_env_var(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A v1.x config (no `session:` wrapper, no `cmd`/`splits`) skips env."""
    workspace = {
        "name": "v1x",
        "windows": [{"name": "main", "panes": [{"commands": ["echo hi"]}]}],
    }
    result = importers.import_teamocil(workspace)
    assert "environment" not in result


def test_import_teamocil_v1x_unknown_pane_keys_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A v1.x pane dict with no recognizable keys warns and produces {}."""
    workspace = {
        "name": "v1x",
        "windows": [{"name": "w", "panes": [{"width": 50}]}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        result = importers.import_teamocil(workspace)
    assert result["windows"][0]["panes"][0] == {}
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and "no recognizable keys" in r.msg
    ]
    assert len(warnings) == 1
    assert getattr(warnings[0], "tmux_key", None) == "width"


def test_import_teamocil_warns_on_v0x_pane_geometry(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """v0.x pane width/height/target each emit WARNING."""
    workspace = {
        "session": {
            "name": "geom",
            "windows": [
                {
                    "name": "w",
                    "splits": [
                        {"cmd": "echo a", "width": 50},
                        {"cmd": "echo b", "height": 30},
                        {"cmd": "echo c", "target": "bottom-right"},
                    ],
                },
            ],
        },
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_teamocil(workspace)
    keys: list[str] = sorted(
        t.cast(str, getattr(r, "tmux_key", ""))
        for r in caplog.records
        if r.levelno == logging.WARNING
        and getattr(r, "tmux_key", None) in {"width", "height", "target"}
    )
    assert keys == ["height", "target", "width"]
