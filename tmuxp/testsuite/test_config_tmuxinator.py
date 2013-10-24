# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import os
import shutil
import unittest
import kaptan
from .. import config, exc
from ..util import tmux

from .. import log
import logging

logger = logging.getLogger(__name__)
TMUXP_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')

# https://github.com/aziz/tmuxinator


class TmuxinatorTest(unittest.TestCase):

    tmuxinator_yaml = """\
    windows:
    - editor:
        layout: main-vertical
        panes:
            - vim
            - guard
    - server: bundle exec rails s
    - logs: tail -f logs/development.log
    """

    tmuxinator_dict = {
        'windows': [
            {
               'editor': {
                    'layout': 'main-vertical',
                    'panes': [
                        'vim',
                        'guard'
                    ]
                }
            },
            {
                'server': 'bundle exec rails s',
            },
            {
                'logs': 'tail -f logs/development.log'
            }
        ]
    }

    def test_config_to_dict(self):
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.tmuxinator_yaml)
        yaml_to_dict = test_config.get()
        self.assertDictEqual(yaml_to_dict, self.tmuxinator_dict)

if __name__ == '__main__':
    unittest.main()
