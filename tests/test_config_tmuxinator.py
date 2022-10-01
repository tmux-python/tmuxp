"""Test for tmuxp tmuxinator configuration."""
import pytest

from tmuxp import config
from tmuxp.config_reader import ConfigReader

from .fixtures import config_tmuxinator as fixtures


@pytest.mark.parametrize(
    "tmuxinator_yaml,tmuxinator_dict,tmuxp_dict",
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
def test_config_to_dict(tmuxinator_yaml, tmuxinator_dict, tmuxp_dict):
    yaml_to_dict = ConfigReader._load(format="yaml", content=tmuxinator_yaml)
    assert yaml_to_dict == tmuxinator_dict

    assert config.import_tmuxinator(tmuxinator_dict) == tmuxp_dict

    config.validate_schema(config.import_tmuxinator(tmuxinator_dict))
