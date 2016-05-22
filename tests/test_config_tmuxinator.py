# -*- coding: utf-8 -*-
"""Test for tmuxp tmuxinator configuration."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import os

import kaptan

from tmuxp import config

from .fixtures import config_tmuxinator as fixtures
from .helpers import TestCase

logger = logging.getLogger(__name__)
TMUXP_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')


class TmuxinatorTest(TestCase):

    tmuxinator_yaml = fixtures.test1.tmuxinator_yaml
    tmuxinator_dict = fixtures.test1.tmuxinator_dict
    tmuxp_dict = fixtures.test1.tmuxp_dict

    def test_config_to_dict(self):
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.tmuxinator_yaml)
        yaml_to_dict = test_config.get()
        assert yaml_to_dict == self.tmuxinator_dict

        assert config.import_tmuxinator(self.tmuxinator_dict) == \
            self.tmuxp_dict


class TmuxinatorDeprecationsTest(TestCase):

    """Tmuxinator uses `tabs` instead of `windows` in older versions.

    https://github.com/aziz/tmuxinator/blob/master/lib/tmuxinator/project.rb#L18

    https://github.com/aziz/tmuxinator/blob/master/spec/fixtures/sample.deprecations.yml

    LICENSE: https://github.com/aziz/tmuxinator/blob/master/LICENSE

    """

    tmuxinator_yaml = fixtures.test2.tmuxinator_yaml
    tmuxinator_dict = fixtures.test2.tmuxinator_dict
    tmuxp_dict = fixtures.test2.tmuxp_dict

    def test_config_to_dict(self):
        self.maxDiff = None
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.tmuxinator_yaml)
        yaml_to_dict = test_config.get()
        assert yaml_to_dict == self.tmuxinator_dict

        assert config.import_tmuxinator(self.tmuxinator_dict) == \
            self.tmuxp_dict


class TmuxinatoriSampleTest(TestCase):

    """Test importing <spec/fixtures/sample.yml>.

    https://github.com/aziz/tmuxinator/blob/master/spec/fixtures/sample.yml

    LICENSE: https://github.com/aziz/tmuxinator/blob/master/LICENSE

    """

    tmuxinator_yaml = fixtures.test3.tmuxinator_yaml
    tmuxinator_dict = fixtures.test3.tmuxinator_dict
    tmuxp_dict = fixtures.test3.tmuxp_dict

    def test_config_to_dict(self):
        self.maxDiff = None
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.tmuxinator_yaml)
        yaml_to_dict = test_config.get()
        assert yaml_to_dict == self.tmuxinator_dict

        assert config.import_tmuxinator(self.tmuxinator_dict) == \
            self.tmuxp_dict
