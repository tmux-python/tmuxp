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
