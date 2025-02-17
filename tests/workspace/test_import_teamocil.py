"""Test for tmuxp teamocil configuration."""

from __future__ import annotations

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
