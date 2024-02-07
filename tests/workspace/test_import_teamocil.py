"""Test for tmuxp teamocil configuration."""
import typing as t

import pytest

from tmuxp._internal import config_reader
from tmuxp.workspace import importers, validation

from ..fixtures import import_teamocil as fixtures


@pytest.mark.parametrize(
    "teamocil_yaml,teamocil_dict,tmuxp_dict",
    [
        (
            fixtures.test1.teamocil_yaml,
            fixtures.test1.teamocil_conf,
            fixtures.test1.expected,
        ),
        (
            fixtures.test2.teamocil_yaml,
            fixtures.test2.teamocil_dict,
            fixtures.test2.expected,
        ),
        (
            fixtures.test3.teamocil_yaml,
            fixtures.test3.teamocil_dict,
            fixtures.test3.expected,
        ),
        (
            fixtures.test4.teamocil_yaml,
            fixtures.test4.teamocil_dict,
            fixtures.test4.expected,
        ),
    ],
)
def test_config_to_dict(
    teamocil_yaml: str,
    teamocil_dict: t.Dict[str, t.Any],
    tmuxp_dict: t.Dict[str, t.Any],
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
def multisession_config() -> (
    t.Dict[
        str,
        t.Dict[str, t.Any],
    ]
):
    """Return loaded multisession teamocil config as a dictionary.

    Also prevents re-running assertion the loads the yaml, since ordering of
    deep list items like panes will be inconsistent.
    """
    teamocil_yaml_file = fixtures.layouts.teamocil_yaml_file
    test_config = config_reader.ConfigReader._from_file(teamocil_yaml_file)
    teamocil_dict: t.Dict[str, t.Any] = fixtures.layouts.teamocil_dict

    assert test_config == teamocil_dict
    return teamocil_dict


@pytest.mark.parametrize(
    "session_name,expected",
    [
        ("two-windows", fixtures.layouts.two_windows),
        ("two-windows-with-filters", fixtures.layouts.two_windows_with_filters),
        (
            "two-windows-with-custom-command-options",
            fixtures.layouts.two_windows_with_custom_command_options,
        ),
        (
            "three-windows-within-a-session",
            fixtures.layouts.three_windows_within_a_session,
        ),
    ],
)
def test_multisession_config(
    session_name: str,
    expected: t.Dict[str, t.Any],
    multisession_config: t.Dict[str, t.Any],
) -> None:
    """Test importing teamocil multisession configuration."""
    # teamocil can fit multiple sessions in a config
    assert importers.import_teamocil(multisession_config[session_name]) == expected

    validation.validate_schema(
        importers.import_teamocil(multisession_config[session_name]),
    )
