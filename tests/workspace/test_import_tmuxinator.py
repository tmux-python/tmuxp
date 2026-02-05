"""Test for tmuxp tmuxinator configuration."""

from __future__ import annotations

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


class PreWindowFixture(t.NamedTuple):
    """Test fixture for pre_window handling tests."""

    test_id: str
    tmuxinator_dict: dict[str, t.Any]
    expected_shell_command: str | list[str] | None
    expected_shell_command_before: list[str] | None


TEST_PRE_WINDOW_FIXTURES: list[PreWindowFixture] = [
    PreWindowFixture(
        test_id="pre_window_alone",
        tmuxinator_dict={
            "name": "test",
            "pre_window": "source .env",
            "windows": [{"editor": "vim"}],
        },
        expected_shell_command=None,
        expected_shell_command_before=["source .env"],
    ),
    PreWindowFixture(
        test_id="pre_window_list_alone",
        tmuxinator_dict={
            "name": "test",
            "pre_window": ["source .env", "cd project"],
            "windows": [{"editor": "vim"}],
        },
        expected_shell_command=None,
        expected_shell_command_before=["source .env", "cd project"],
    ),
    PreWindowFixture(
        test_id="pre_tab_alone",
        tmuxinator_dict={
            "name": "test",
            "pre_tab": "source .env",
            "windows": [{"editor": "vim"}],
        },
        expected_shell_command=None,
        expected_shell_command_before=["source .env"],
    ),
    PreWindowFixture(
        test_id="pre_and_pre_window",
        tmuxinator_dict={
            "name": "test",
            "pre": "cd /project",
            "pre_window": "source .env",
            "windows": [{"editor": "vim"}],
        },
        expected_shell_command="cd /project",
        expected_shell_command_before=["source .env"],
    ),
    PreWindowFixture(
        test_id="pre_alone",
        tmuxinator_dict={
            "name": "test",
            "pre": "source .env",
            "windows": [{"editor": "vim"}],
        },
        expected_shell_command=None,
        expected_shell_command_before=["source .env"],
    ),
]


@pytest.mark.parametrize(
    "test",
    TEST_PRE_WINDOW_FIXTURES,
    ids=[test.test_id for test in TEST_PRE_WINDOW_FIXTURES],
)
def test_pre_window_handling(test: PreWindowFixture) -> None:
    """Test pre_window/pre_tab handling in tmuxinator import."""
    result = importers.import_tmuxinator(test.tmuxinator_dict.copy())

    if test.expected_shell_command:
        assert result.get("shell_command") == test.expected_shell_command
    else:
        assert "shell_command" not in result

    if test.expected_shell_command_before:
        assert result.get("shell_command_before") == test.expected_shell_command_before
    else:
        assert "shell_command_before" not in result


class VersionManagerFixture(t.NamedTuple):
    """Test fixture for rbenv/rvm handling tests."""

    test_id: str
    tmuxinator_dict: dict[str, t.Any]
    expected_shell_command_before: list[str]


TEST_VERSION_MANAGER_FIXTURES: list[VersionManagerFixture] = [
    VersionManagerFixture(
        test_id="rbenv_only",
        tmuxinator_dict={
            "name": "test",
            "rbenv": "2.7.0",
            "windows": [{"editor": "vim"}],
        },
        expected_shell_command_before=["rbenv shell 2.7.0"],
    ),
    VersionManagerFixture(
        test_id="rvm_only",
        tmuxinator_dict={
            "name": "test",
            "rvm": "2.7.0",
            "windows": [{"editor": "vim"}],
        },
        expected_shell_command_before=["rvm use 2.7.0"],
    ),
    VersionManagerFixture(
        test_id="rbenv_with_pre_window",
        tmuxinator_dict={
            "name": "test",
            "pre_window": "source .env",
            "rbenv": "3.0.0",
            "windows": [{"editor": "vim"}],
        },
        expected_shell_command_before=["source .env", "rbenv shell 3.0.0"],
    ),
    VersionManagerFixture(
        test_id="rvm_with_pre_window",
        tmuxinator_dict={
            "name": "test",
            "pre_window": "source .env",
            "rvm": "3.0.0",
            "windows": [{"editor": "vim"}],
        },
        expected_shell_command_before=["source .env", "rvm use 3.0.0"],
    ),
]


@pytest.mark.parametrize(
    "test",
    TEST_VERSION_MANAGER_FIXTURES,
    ids=[test.test_id for test in TEST_VERSION_MANAGER_FIXTURES],
)
def test_version_manager_handling(test: VersionManagerFixture) -> None:
    """Test rbenv/rvm handling in tmuxinator import."""
    result = importers.import_tmuxinator(test.tmuxinator_dict.copy())

    assert result.get("shell_command_before") == test.expected_shell_command_before
