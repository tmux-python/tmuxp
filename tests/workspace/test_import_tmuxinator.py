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


class SynchronizeFixture(t.NamedTuple):
    """Test fixture for synchronize handling tests."""

    test_id: str
    tmuxinator_dict: dict[str, t.Any]
    expected_options: dict[str, str] | None
    expected_options_after: dict[str, str] | None


TEST_SYNCHRONIZE_FIXTURES: list[SynchronizeFixture] = [
    SynchronizeFixture(
        test_id="synchronize_true",
        tmuxinator_dict={
            "name": "test",
            "windows": [{"editor": {"panes": ["vim"], "synchronize": True}}],
        },
        expected_options={"synchronize-panes": "on"},
        expected_options_after=None,
    ),
    SynchronizeFixture(
        test_id="synchronize_before",
        tmuxinator_dict={
            "name": "test",
            "windows": [{"editor": {"panes": ["vim"], "synchronize": "before"}}],
        },
        expected_options={"synchronize-panes": "on"},
        expected_options_after=None,
    ),
    SynchronizeFixture(
        test_id="synchronize_after",
        tmuxinator_dict={
            "name": "test",
            "windows": [{"editor": {"panes": ["vim"], "synchronize": "after"}}],
        },
        expected_options=None,
        expected_options_after={"synchronize-panes": "on"},
    ),
    SynchronizeFixture(
        test_id="synchronize_false",
        tmuxinator_dict={
            "name": "test",
            "windows": [{"editor": {"panes": ["vim"], "synchronize": False}}],
        },
        expected_options=None,
        expected_options_after=None,
    ),
]


@pytest.mark.parametrize(
    "test",
    TEST_SYNCHRONIZE_FIXTURES,
    ids=[test.test_id for test in TEST_SYNCHRONIZE_FIXTURES],
)
def test_synchronize_handling(test: SynchronizeFixture) -> None:
    """Test synchronize handling in tmuxinator import."""
    result = importers.import_tmuxinator(test.tmuxinator_dict.copy())

    window = result["windows"][0]
    if test.expected_options:
        assert window.get("options") == test.expected_options
    else:
        assert "options" not in window

    if test.expected_options_after:
        assert window.get("options_after") == test.expected_options_after
    else:
        assert "options_after" not in window


class StartupFixture(t.NamedTuple):
    """Test fixture for startup_window/startup_pane handling tests."""

    test_id: str
    tmuxinator_dict: dict[str, t.Any]
    expected_focused_window: str | None
    expected_focused_pane_index: int | None


TEST_STARTUP_FIXTURES: list[StartupFixture] = [
    StartupFixture(
        test_id="startup_window",
        tmuxinator_dict={
            "name": "test",
            "startup_window": "logs",
            "windows": [
                {"editor": "vim"},
                {"logs": "tail -f log.txt"},
            ],
        },
        expected_focused_window="logs",
        expected_focused_pane_index=None,
    ),
    StartupFixture(
        test_id="startup_pane",
        tmuxinator_dict={
            "name": "test",
            "startup_pane": 1,
            "windows": [{"editor": {"panes": ["vim", "git status", "htop"]}}],
        },
        expected_focused_window=None,
        expected_focused_pane_index=1,
    ),
    StartupFixture(
        test_id="startup_window_and_pane",
        tmuxinator_dict={
            "name": "test",
            "startup_window": "editor",
            "startup_pane": 2,
            "windows": [
                {"editor": {"panes": ["vim", "git status", "htop"]}},
                {"logs": "tail -f log.txt"},
            ],
        },
        expected_focused_window="editor",
        expected_focused_pane_index=2,
    ),
    StartupFixture(
        test_id="startup_window_not_found",
        tmuxinator_dict={
            "name": "test",
            "startup_window": "nonexistent",
            "windows": [{"editor": "vim"}],
        },
        expected_focused_window=None,
        expected_focused_pane_index=None,
    ),
]


@pytest.mark.parametrize(
    "test",
    TEST_STARTUP_FIXTURES,
    ids=[test.test_id for test in TEST_STARTUP_FIXTURES],
)
def test_startup_handling(test: StartupFixture) -> None:
    """Test startup_window/startup_pane handling in tmuxinator import."""
    result = importers.import_tmuxinator(test.tmuxinator_dict.copy())

    # Check focused window
    focused_windows = [w for w in result["windows"] if w.get("focus")]
    if test.expected_focused_window:
        assert len(focused_windows) == 1
        assert focused_windows[0]["window_name"] == test.expected_focused_window
    else:
        # No window should be focused (unless startup_pane sets implicit focus)
        if test.expected_focused_pane_index is None:
            assert len(focused_windows) == 0

    # Check focused pane
    if test.expected_focused_pane_index is not None:
        # Find the window that should contain the focused pane
        if test.expected_focused_window:
            target_window = next(
                w
                for w in result["windows"]
                if w["window_name"] == test.expected_focused_window
            )
        else:
            target_window = result["windows"][0]

        panes = target_window.get("panes", [])
        focused_pane = panes[test.expected_focused_pane_index]
        assert isinstance(focused_pane, dict)
        assert focused_pane.get("focus") is True


def test_post_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Test that 'post' key triggers a warning."""
    tmuxinator_dict = {
        "name": "test",
        "post": "echo 'session started'",
        "windows": [{"editor": "vim"}],
    }

    with caplog.at_level("WARNING", logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(tmuxinator_dict.copy())

    assert any("post" in record.message for record in caplog.records)
    assert any("not supported" in record.message for record in caplog.records)
