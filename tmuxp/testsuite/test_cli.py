# -*- coding: utf-8 -*-
"""Test for tmuxp command line interface.

tmuxp.tests.test_cli
~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2013 Tony Narlock.
:license: BSD, see LICENSE for details

"""
from __future__ import absolute_import, division, print_function, with_statement

import os
import shutil
import kaptan
import tempfile
from .. import config, cli
from ..util import tmux
from .helpers import TestCase

import logging

logger = logging.getLogger(__name__)
TMUXP_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')


class StartupTest(TestCase):

    """test startup_cli()."""

    def setUp(self):
        if os.path.isdir(TMUXP_DIR):
            shutil.rmtree(TMUXP_DIR)

    def test_creates_config_dir_not_exists(self):
        """cli.startup() creates config dir if not exists."""

        self.assertFalse(os.path.exists(TMUXP_DIR))
        cli.startup(TMUXP_DIR)

        self.assertTrue(os.path.exists(TMUXP_DIR))

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(TMUXP_DIR):
            shutil.rmtree(TMUXP_DIR)
        logger.debug('wiped %s' % TMUXP_DIR)


class FindConfigsTest(TestCase):

    """test in_dir() test."""

    def setUp(self):
        if os.path.isdir(TMUXP_DIR):
            shutil.rmtree(TMUXP_DIR)

    def test_in_dir_from_config_dir(self):
        """config.in_dir() finds configs config dir."""

        cli.startup(TMUXP_DIR)
        config1 = tempfile.NamedTemporaryFile(
            dir=TMUXP_DIR,
            prefix='myconfig',
            suffix='.yaml'
        )

        config2 = tempfile.NamedTemporaryFile(
            dir=TMUXP_DIR,
            prefix='myconfig',
            suffix='.json'
        )
        configs_found = config.in_dir(TMUXP_DIR)

        self.assertEqual(len(configs_found), 2)

    def test_in_dir_from_current_dir(self):
        """config.in_dir() find configs config dir."""

        cli.startup(TMUXP_DIR)
        config1 = tempfile.NamedTemporaryFile(
            dir=TMUXP_DIR,
            prefix='myconfig',
            suffix='.yaml'
        )

        config2 = tempfile.NamedTemporaryFile(
            dir=TMUXP_DIR,
            prefix='myconfig',
            suffix='.json'
        )
        configs_found = config.in_dir(TMUXP_DIR)

        self.assertEqual(len(configs_found), 2)

    def test_ignore_non_configs_from_current_dir(self):
        """cli.in_dir() ignore non-config from config dir."""

        cli.startup(TMUXP_DIR)
        badconfig = tempfile.NamedTemporaryFile(
            dir=TMUXP_DIR,
            prefix='myconfig',
            suffix='.psd'
        )

        config1 = tempfile.NamedTemporaryFile(
            dir=TMUXP_DIR,
            prefix='watmyconfig',
            suffix='.json'
        )
        configs_found = config.in_dir(TMUXP_DIR)

        self.assertEqual(len(configs_found), 1)

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

        self.assertEqual(len(configs_found), 1)
        self.assertIn('.tmuxp.json', configs_found)

        # clean up
        os.chdir(current_dir)
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(TMUXP_DIR):
            shutil.rmtree(TMUXP_DIR)
        logger.debug('wiped %s' % TMUXP_DIR)

sampleconfigdict = {
    'session_name': 'sampleconfig',
    'start_directory': '~',
    'windows': [
        {
            'window_name': 'editor',
            'panes': [
                {
                    'start_directory': '~',
                    'shell_command': ['vim'],
                },
                {
                    'shell_command': ['cowsay "hey"']
                },
            ],
            'layout': 'main-verticle'
        },
        {
            'window_name': 'logging', 'panes': [
                {
                    'shell_command': ['tail -F /var/log/syslog'],
                    'start_directory':'/var/log'
                }
            ]
        }, {
            'options': {'automatic_rename': True, },
            'panes': [
                {
                    'shell_command': ['htop']
                }
            ]
        }
    ]
}
