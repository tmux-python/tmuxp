# -*- coding: utf-8 -*-
"""Test for tmuxp command line interface."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import os
import shutil
import tempfile

from tmuxp import cli, config

from .helpers import TestCase

logger = logging.getLogger(__name__)


class StartupTest(TestCase):

    """test startup_cli()."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(suffix='tmuxp')
        if os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_creates_config_dir_not_exists(self):
        """cli.startup() creates config dir if not exists."""

        assert not os.path.exists(self.tmp_dir)
        cli.startup(self.tmp_dir)

        assert os.path.exists(self.tmp_dir)

    def tearDown(self):
        if os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
        logger.debug('wiped %s' % self.tmp_dir)


class FindConfigsTest(TestCase):

    """test in_dir() test."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(suffix='tmuxp')
        if os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_in_dir_from_config_dir(self):
        """config.in_dir() finds configs config dir."""

        cli.startup(self.tmp_dir)
        with tempfile.NamedTemporaryFile(
            dir=self.tmp_dir,
            prefix='myconfig',
            suffix='.yaml'
        ):
            with tempfile.NamedTemporaryFile(
                dir=self.tmp_dir,
                prefix='myconfig',
                suffix='.json'
            ):
                configs_found = config.in_dir(self.tmp_dir)

                assert len(configs_found) == 2

    def test_in_dir_from_current_dir(self):
        """config.in_dir() find configs current dir."""
        pass  # TODO

    def test_ignore_non_configs_from_current_dir(self):
        """cli.in_dir() ignore non-config from config dir."""

        cli.startup(self.tmp_dir)
        with tempfile.NamedTemporaryFile(
            dir=self.tmp_dir,
            prefix='myconfig',
            suffix='.psd'
        ):
            with tempfile.NamedTemporaryFile(
                dir=self.tmp_dir,
                prefix='watmyconfig',
                suffix='.json'
            ):
                configs_found = config.in_dir(self.tmp_dir)
                assert len(configs_found) == 1

    def test_get_configs_cwd(self):
        """config.in_cwd() find config in shell current working directory."""

        current_dir = os.getcwd()

        configs_found = config.in_cwd()

        # create a temporary folder and change dir into it
        tmp_dir = tempfile.mkdtemp(suffix='tmuxp')
        os.chdir(tmp_dir)

        try:
            config1 = open('.tmuxp.json', 'w+b')
            config1.close()

            configs_found = config.in_cwd()
        finally:
            os.remove(config1.name)

        assert len(configs_found) == 1
        assert '.tmuxp.json' in configs_found

        # clean up
        os.chdir(current_dir)
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)

    def tearDown(self):
        if os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
        logger.debug('wiped %s' % self.tmp_dir)
