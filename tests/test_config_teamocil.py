# -*- coding: utf-8 -*-
"""Test for tmuxp teamocil configuration."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import os

import kaptan

from tmuxp import config

from .helpers import TestCase
from .fixtures import config_teamocil as fixtures

logger = logging.getLogger(__name__)
TMUXP_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')


class TeamocilTest(TestCase):

    teamocil_yaml = fixtures.test1.teamocil_yaml
    teamocil_dict = fixtures.test1.teamocil_conf
    tmuxp_dict = fixtures.test1.expected

    def test_config_to_dict(self):
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.teamocil_yaml)
        yaml_to_dict = test_config.get()
        assert yaml_to_dict == self.teamocil_dict
        assert config.import_teamocil(self.teamocil_dict) == self.tmuxp_dict

        config.validate_schema(
            config.import_teamocil(
                self.teamocil_dict
            )
        )


class Teamocil2Test(TestCase):

    teamocil_yaml = fixtures.test2.teamocil_yaml
    teamocil_dict = fixtures.test2.teamocil_dict
    tmuxp_dict = fixtures.test2.expected

    def test_config_to_dict(self):
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.teamocil_yaml)
        yaml_to_dict = test_config.get()
        assert yaml_to_dict == self.teamocil_dict

        assert config.import_teamocil(self.teamocil_dict) == self.tmuxp_dict

        config.validate_schema(
            config.import_teamocil(
                self.teamocil_dict
            )
        )


class Teamocil3Test(TestCase):

    teamocil_yaml = fixtures.test3.teamocil_yaml
    teamocil_dict = fixtures.test3.teamocil_dict
    tmuxp_dict = fixtures.test3.expected

    def test_config_to_dict(self):
        self.maxDiff = None
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.teamocil_yaml)
        yaml_to_dict = test_config.get()
        assert yaml_to_dict == self.teamocil_dict

        assert config.import_teamocil(self.teamocil_dict) == self.tmuxp_dict

        config.validate_schema(
            config.import_teamocil(
                self.teamocil_dict
            )
        )


class Teamocil4Test(TestCase):

    teamocil_yaml = fixtures.test4.teamocil_yaml
    teamocil_dict = fixtures.test4.teamocil_dict
    tmuxp_dict = fixtures.test4.expected

    def test_config_to_dict(self):
        self.maxDiff = None
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.teamocil_yaml)
        yaml_to_dict = test_config.get()
        assert yaml_to_dict == self.teamocil_dict

        assert config.import_teamocil(self.teamocil_dict) == self.tmuxp_dict

        config.validate_schema(
            config.import_teamocil(
                self.teamocil_dict
            )
        )


class TeamocilLayoutsTest(TestCase):

    """Import configurations from teamocil's <fixtures/layout.yml>.

    https://github.com/remiprev/teamocil/blob/master/spec/fixtures/layouts.yml

    LICENSE: https://github.com/remiprev/teamocil/blob/master/LICENSE

    """

    teamocil_yaml = fixtures.layouts.teamocil_yaml
    teamocil_dict = fixtures.layouts.teamocil_dict
    two_windows = fixtures.layouts.two_windows
    two_windows_with_filters = fixtures.layouts.two_windows_with_filters
    two_windows_with_custom_command_options = \
        fixtures.layouts.two_windows_with_custom_command_options
    three_windows_within_a_session = \
        fixtures.layouts.three_windows_within_a_session

    def test_config_to_dict(self):
        self.maxDiff = None
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.teamocil_yaml)
        yaml_to_dict = test_config.get()
        assert yaml_to_dict == self.teamocil_dict

        assert config.import_teamocil(self.teamocil_dict['two-windows']) == \
            self.two_windows

        config.validate_schema(
            config.import_teamocil(
                self.teamocil_dict['two-windows']
            )
        )

        assert config.import_teamocil(
            self.teamocil_dict['two-windows-with-filters'],
        ) == self.two_windows_with_filters

        config.validate_schema(
            config.import_teamocil(
                self.teamocil_dict['two-windows-with-filters']
            )
        )

        assert config.import_teamocil(
            self.teamocil_dict['two-windows-with-custom-command-options'],
        ) == self.two_windows_with_custom_command_options

        config.validate_schema(
            config.import_teamocil(
                self.teamocil_dict['two-windows-with-custom-command-options']
            )
        )

        assert config.import_teamocil(
            self.teamocil_dict['three-windows-within-a-session'],
        ) == self.three_windows_within_a_session

        config.validate_schema(
            config.import_teamocil(
                self.teamocil_dict['three-windows-within-a-session']
            )
        )

        # this configuration contains multiple sessions in a single file.
        # tmuxp can split them into files, proceed?
