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
        test_id="pre_alone",  # solo pre -> before_script
        tmuxinator_yaml=fixtures.test_pre_alone.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test_pre_alone.tmuxinator_dict,
        tmuxp_dict=fixtures.test_pre_alone.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="pre_combo",  # pre + pre_window map independently
        tmuxinator_yaml=fixtures.test_pre_combo.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test_pre_combo.tmuxinator_dict,
        tmuxp_dict=fixtures.test_pre_combo.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="pre_shell_metachars",  # warning when pre has shell constructs
        tmuxinator_yaml=fixtures.test_pre_shell.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test_pre_shell.tmuxinator_dict,
        tmuxp_dict=fixtures.test_pre_shell.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="cli_args_multi_flags",  # -f/-L/-S all extracted
        tmuxinator_yaml=fixtures.test_cli_args_multi.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test_cli_args_multi.tmuxinator_dict,
        tmuxp_dict=fixtures.test_cli_args_multi.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="cli_args_dash_in_path",  # regression: -f in path doesn't corrupt
        tmuxinator_yaml=fixtures.test_cli_args_dash_path.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test_cli_args_dash_path.tmuxinator_dict,
        tmuxp_dict=fixtures.test_cli_args_dash_path.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="rvm",  # rvm wrapped as `rvm use <ver>`
        tmuxinator_yaml=fixtures.test_rvm.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test_rvm.tmuxinator_dict,
        tmuxp_dict=fixtures.test_rvm.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="startup_window_by_name",  # name -> focus
        tmuxinator_yaml=fixtures.test_startup_window_by_name.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test_startup_window_by_name.tmuxinator_dict,
        tmuxp_dict=fixtures.test_startup_window_by_name.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="startup_window_by_index",  # int -> focus
        tmuxinator_yaml=fixtures.test_startup_window_by_index.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test_startup_window_by_index.tmuxinator_dict,
        tmuxp_dict=fixtures.test_startup_window_by_index.expected,
    ),
    TmuxinatorConfigTestFixture(
        test_id="socket_path",  # socket_path passes through
        tmuxinator_yaml=fixtures.test_socket_path.tmuxinator_yaml,
        tmuxinator_dict=fixtures.test_socket_path.tmuxinator_dict,
        tmuxp_dict=fixtures.test_socket_path.expected,
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


def test_import_tmuxinator_warns_on_shell_metachars_in_pre(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`pre` containing shell constructs emits WARNING with tmux_key=pre."""
    workspace = {
        "name": "shell-pre",
        "pre": "echo a | grep b && echo done",
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(workspace)
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and getattr(r, "tmux_key", None) == "pre"
    ]
    assert len(warnings) == 1
    assert getattr(warnings[0], "tmux_session", None) == "shell-pre"


def test_import_tmuxinator_no_warning_when_pre_is_plain(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A `pre` value without shell metacharacters emits no warning."""
    workspace = {
        "name": "plain-pre",
        "pre": "sudo /etc/rc.d/mysqld start",
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(workspace)
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and getattr(r, "tmux_key", None) == "pre"
    ]
    assert warnings == []


def test_import_tmuxinator_warns_on_unknown_cli_args_flag(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unrecognized tmux flag in cli_args emits a WARNING."""
    workspace = {
        "name": "weird",
        "cli_args": "-f ~/.tmux.conf -X bogus",
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(workspace)
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and getattr(r, "tmux_key", None) == "-X"
    ]
    assert len(warnings) == 1
    assert getattr(warnings[0], "tmux_session", None) == "weird"


def test_import_tmuxinator_warns_on_attach_false(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`attach: false` emits WARNING directing user to CLI `-d` flag."""
    workspace = {
        "name": "no-attach",
        "attach": False,
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(workspace)
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and getattr(r, "tmux_key", None) == "attach"
    ]
    assert len(warnings) == 1


def test_import_tmuxinator_on_project_first_start_falls_back_to_pre(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`on_project_first_start` maps to before_script when `pre` absent."""
    workspace = {
        "name": "fallback",
        "on_project_first_start": "echo first",
        "windows": [{"editor": "vim"}],
    }
    result = importers.import_tmuxinator(workspace)
    assert result["before_script"] == "echo first"


def test_import_tmuxinator_pre_window_chain_first_match_wins(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Rbenv wins over rvm/pre_tab/pre_window per project.rb:175-188."""
    workspace = {
        "name": "chain",
        "rbenv": "2.7.0",
        "rvm": "3.2.0",
        "pre_tab": "echo pre_tab",
        "pre_window": "echo pre_window",
        "windows": [{"editor": "vim"}],
    }
    result = importers.import_tmuxinator(workspace)
    assert result["shell_command_before"] == ["rbenv shell 2.7.0"]


def test_import_tmuxinator_warns_on_unresolved_startup_window(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unresolvable `startup_window` value emits WARNING."""
    workspace = {
        "name": "miss",
        "startup_window": "nonexistent",
        "windows": [{"editor": "vim"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(workspace)
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and getattr(r, "tmux_key", None) == "startup_window"
    ]
    assert len(warnings) == 1


def test_import_tmuxinator_warns_on_out_of_range_startup_window_int(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An integer `startup_window` past the window count emits WARNING."""
    workspace = {
        "name": "oor",
        "startup_window": 99,
        "windows": [{"editor": "vim"}, {"shell": "bash"}],
    }
    with caplog.at_level(logging.WARNING, logger="tmuxp.workspace.importers"):
        importers.import_tmuxinator(workspace)
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and getattr(r, "tmux_key", None) == "startup_window"
    ]
    assert len(warnings) == 1
