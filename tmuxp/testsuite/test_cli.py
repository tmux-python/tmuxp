# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import os
import shutil
import unittest
import kaptan
from .. import config, cli
from ..util import tmux

from .. import log
import logging

logger = logging.getLogger(__name__)
TMUXP_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')


class StartupTest(unittest.TestCase):
    '''test startup_cli()'''

    def setUp(self):
        if os.path.isdir(TMUXP_DIR):
            shutil.rmtree(TMUXP_DIR)

    def test_creates_config_dir_not_exists(self):
        '''cli.startup() creates config dir if not exists'''

        self.assertFalse(os.path.exists(TMUXP_DIR))
        cli.startup(TMUXP_DIR)

        self.assertTrue(os.path.exists(TMUXP_DIR))

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(TMUXP_DIR):
            shutil.rmtree(TMUXP_DIR)
        logging.debug('wiped %s' % TMUXP_DIR)

sampleconfigdict = {
    'session_name': 'sampleconfig',
    'start_directory': '~',
    'windows': [{
        'window_name': 'editor',
        'panes': [
            {
                'start_directory': '~', 'shell_command': ['vim'],
                },  {
                'shell_command': ['cowsay "hey"']
            },
        ],
        'layout': 'main-verticle'},
        {'window_name': 'logging', 'panes': [
         {'shell_command': ['tail -F /var/log/syslog'],
          'start_directory':'/var/log'}
         ]}, {
            'automatic_rename': True,
            'panes': [
                {'shell_command': ['htop']}
            ]
        }]
}

if __name__ == '__main__':
    unittest.main()
