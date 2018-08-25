# -*- coding: utf-8 -*-
"""Test for tmuxp tmuxinator configuration."""

from __future__ import absolute_import, unicode_literals

import os

import pytest

import kaptan

from tmuxp import config

from .fixtures import config_tmuxinator as fixtures

TMUXP_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')


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
    configparser = kaptan.Kaptan(handler='yaml')
    test_config = configparser.import_config(tmuxinator_yaml)
    yaml_to_dict = test_config.get()
    assert yaml_to_dict == tmuxinator_dict

    assert config.import_tmuxinator(tmuxinator_dict) == tmuxp_dict

    config.validate_schema(config.import_tmuxinator(tmuxinator_dict))
