"""Test for tmuxp tmuxinator configuration."""

import typing as t

import pytest

from tests.fixtures import import_tmuxinator as fixtures
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.workspace import importers, validation


@pytest.mark.parametrize(
    ("tmuxinator_yaml", "tmuxinator_dict", "tmuxp_dict"),
    [
        (
            fixtures.test1.tmuxinator_yaml,
            fixtures.test1.tmuxinator_dict,
            fixtures.test1.expected,
        ),
        (
            fixtures.test2.tmuxinator_yaml,
            fixtures.test2.tmuxinator_dict,
            fixtures.test2.expected,
        ),  # older vers use `tabs` instead of `windows`
        (
            fixtures.test3.tmuxinator_yaml,
            fixtures.test3.tmuxinator_dict,
            fixtures.test3.expected,
        ),  # Test importing <spec/fixtures/sample.yml>
    ],
)
def test_config_to_dict(
    tmuxinator_yaml: str,
    tmuxinator_dict: t.Dict[str, t.Any],
    tmuxp_dict: t.Dict[str, t.Any],
) -> None:
    """Test exporting tmuxinator configuration to dictionary."""
    yaml_to_dict = ConfigReader._load(fmt="yaml", content=tmuxinator_yaml)
    assert yaml_to_dict == tmuxinator_dict

    assert importers.import_tmuxinator(tmuxinator_dict) == tmuxp_dict

    validation.validate_schema(importers.import_tmuxinator(tmuxinator_dict))
