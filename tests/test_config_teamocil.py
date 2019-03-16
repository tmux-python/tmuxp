# -*- coding: utf-8 -*-
"""Test for tmuxp teamocil configuration."""

from __future__ import absolute_import, unicode_literals

import os

import pytest

import kaptan

from tmuxp import config

from .fixtures import config_teamocil as fixtures

TMUXP_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')


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
def test_config_to_dict(teamocil_yaml, teamocil_dict, tmuxp_dict):
    configparser = kaptan.Kaptan(handler='yaml')
    test_config = configparser.import_config(teamocil_yaml)
    yaml_to_dict = test_config.get()
    assert yaml_to_dict == teamocil_dict

    assert config.import_teamocil(teamocil_dict) == tmuxp_dict

    config.validate_schema(config.import_teamocil(teamocil_dict))


@pytest.fixture(scope='module')
def multisession_config():
    """Return loaded multisession teamocil config as a dictionary.

    Also prevents re-running assertion the loads the yaml, since ordering of
    deep list items like panes will be inconsistent."""
    teamocil_yaml = fixtures.layouts.teamocil_yaml
    configparser = kaptan.Kaptan(handler='yaml')
    test_config = configparser.import_config(teamocil_yaml)
    teamocil_dict = fixtures.layouts.teamocil_dict

    assert test_config.get() == teamocil_dict
    return teamocil_dict


@pytest.mark.parametrize(
    "session_name,expected",
    [
        ('two-windows', fixtures.layouts.two_windows),
        ('two-windows-with-filters', fixtures.layouts.two_windows_with_filters),
        (
            'two-windows-with-custom-command-options',
            fixtures.layouts.two_windows_with_custom_command_options,
        ),
        (
            'three-windows-within-a-session',
            fixtures.layouts.three_windows_within_a_session,
        ),
    ],
)
def test_multisession_config(session_name, expected, multisession_config):
    # teamocil can fit multiple sessions in a config
    assert config.import_teamocil(multisession_config[session_name]) == expected

    config.validate_schema(config.import_teamocil(multisession_config[session_name]))
