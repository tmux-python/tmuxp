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
        test_id="v1_string_panes",
        teamocil_yaml=fixtures.test5.teamocil_yaml,
        teamocil_dict=fixtures.test5.teamocil_dict,
        tmuxp_dict=fixtures.test5.expected,
    ),
    TeamocilConfigTestFixture(
        test_id="focus_and_options",
        teamocil_yaml=fixtures.test6.teamocil_yaml,
        teamocil_dict=fixtures.test6.teamocil_dict,
        tmuxp_dict=fixtures.test6.expected,
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


class TeamocilPaneConversionFixture(t.NamedTuple):
    """Test fixture for teamocil pane conversion."""

    test_id: str
    pane_config: t.Any
    expected_pane: dict[str, t.Any]


TEAMOCIL_PANE_CONVERSION_FIXTURES: list[TeamocilPaneConversionFixture] = [
    TeamocilPaneConversionFixture(
        test_id="string-pane",
        pane_config="echo hi",
        expected_pane={"shell_command": ["echo hi"]},
    ),
    TeamocilPaneConversionFixture(
        test_id="blank-pane",
        pane_config=None,
        expected_pane={"shell_command": []},
    ),
    TeamocilPaneConversionFixture(
        test_id="commands-key",
        pane_config={"commands": ["pwd", "ls"]},
        expected_pane={"shell_command": ["pwd", "ls"]},
    ),
]


@pytest.mark.parametrize(
    list(TeamocilPaneConversionFixture._fields),
    TEAMOCIL_PANE_CONVERSION_FIXTURES,
    ids=[test.test_id for test in TEAMOCIL_PANE_CONVERSION_FIXTURES],
)
def test_import_teamocil_pane_conversion(
    test_id: str,
    pane_config: t.Any,
    expected_pane: dict[str, t.Any],
) -> None:
    """Teamocil panes normalize to tmuxp pane dictionaries."""
    workspace = {
        "windows": [
            {
                "name": "main",
                "panes": [pane_config],
            }
        ],
    }

    result = importers.import_teamocil(workspace)

    assert result["windows"][0]["panes"] == [expected_pane]


def test_import_teamocil_warns_and_drops_pane_dimensions(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unsupported width/height pane keys are dropped with warnings."""
    workspace = {
        "windows": [
            {
                "name": "main",
                "panes": [{"cmd": "vim", "width": 30, "height": 20}],
            }
        ],
    }

    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        result = importers.import_teamocil(workspace)

    assert result["windows"][0]["panes"] == [{"shell_command": "vim"}]
    assert any("width" in record.message for record in caplog.records)
    assert any("height" in record.message for record in caplog.records)
