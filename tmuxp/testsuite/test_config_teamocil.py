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


class TeamocilTest(unittest.TestCase):

    teamocil_yaml = """\
    windows:
    - name: "sample-two-panes"
      root: "~/Code/sample/www"
      layout: even-horizontal
      panes:
        - cmd: ["pwd", "ls -la"]
        - cmd: "rails server --port 3000"
    """

    teamocil_dict = {
        'windows': [{
            'name': 'sample-two-panes',
            'root': '~/Code/sample/www',
            'layout': 'even-horizontal',
            'panes': [
                {'cmd': [
                    'pwd',
                    'ls -la'
                    ]
                 },
                {'cmd': 'rails server --port 3000'}
            ]
        }]
    }

    def test_config_to_dict(self):
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.teamocil_yaml)
        yaml_to_dict = test_config.get()
        self.assertDictEqual(yaml_to_dict, self.teamocil_dict)

    def test_config_to_yaml(self):
        '''teamocil yaml to tmuxp yaml config

        use check_consistency to assert against
        '''
        pass


class Teamocil2Test(unittest.TestCase):

    teamocil_yaml = """\
    windows:
    - name: "sample-four-panes"
      root: "~/Code/sample/www"
      layout: tiled
      panes:
        - cmd: "pwd"
        - cmd: "pwd"
        - cmd: "pwd"
        - cmd: "pwd"
    """

    teamocil_dict = {
        'windows': [{
            'name': 'sample-four-panes',
            'root': '~/Code/sample/www',
            'layout': 'tiled',
            'panes': [
                {'cmd': 'pwd'},
                {'cmd': 'pwd'},
                {'cmd': 'pwd'},
                {'cmd': 'pwd'},
            ]
        }]
    }

    def test_config_to_dict(self):
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.teamocil_yaml)
        yaml_to_dict = test_config.get()
        self.assertDictEqual(yaml_to_dict, self.teamocil_dict)


class Teamocil3Test(unittest.TestCase):

    teamocil_yaml = """\
    windows:
    - name: "my-first-window"
      root: "~/Projects/foo-www"
      layout: even-vertical
      filters:
        before: "rbenv local 2.0.0-p0"
        after: "echo 'I am done initializing this pane.'"
      panes:
        - cmd: "git status"
        - cmd: "bundle exec rails server --port 4000"
          focus: true
        - cmd:
          - "sudo service memcached start"
          - "sudo service mongodb start"
    """

    teamocil_dict = {
        'windows': [{
            'name': 'my-first-window',
            'root': '~/Projects/foo-www',
            'layout': 'even-vertical',
            'filters': {
                'before': 'rbenv local 2.0.0-p0',
                'after': 'echo \'I am done initializing this pane.\''
            },
            'panes': [
                {'cmd': 'git status'},
                {'cmd': 'bundle exec rails server --port 4000',
                    'focus': True},
                {'cmd': [
                    'sudo service memcached start',
                    'sudo service mongodb start',
                ]}
            ]
        }]
    }

    def test_config_to_dict(self):
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.teamocil_yaml)
        yaml_to_dict = test_config.get()
        self.assertDictEqual(yaml_to_dict, self.teamocil_dict)


class Teamocil4Test(unittest.TestCase):

    teamocil_yaml = """\
    windows:
    - name: "erb-example"
      root: <%= ENV['MY_PROJECT_ROOT'] %>
      panes:
        - cmd: "pwd"
    """

    teamocil_dict = {
        'windows': [{
            'name': 'erb-example',
            'root': "<%= ENV['MY_PROJECT_ROOT'] %>",
            'panes': [
                {'cmd': 'pwd'}
            ]
        }]
    }

    def test_config_to_dict(self):
        self.maxDiff = None
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.teamocil_yaml)
        yaml_to_dict = test_config.get()
        self.assertDictEqual(yaml_to_dict, self.teamocil_dict)


class TeamocilLayoutsTest(unittest.TestCase):

    '''

    https://github.com/remiprev/teamocil/blob/master/spec/fixtures/layouts.yml

    LICENSE: https://github.com/remiprev/teamocil/blob/master/LICENSE
    '''

    teamocil_yaml = """\
    # Simple two windows layout
    two-windows:
        windows:
          - name: "foo"
            clear: true
            root: "/foo"
            layout: "tiled"
            panes:
              - cmd: "echo 'foo'"
              - cmd: "echo 'foo again'"
          - name: "bar"
            root: "/bar"
            splits:
              - cmd:
                - "echo 'bar'"
                - "echo 'bar in an array'"
                target: bottom-right
              - cmd: "echo 'bar again'"
                focus: true
                width: 50

    # Simple two windows layout with filters
    two-windows-with-filters:
        windows:
          - name: "foo"
            root: "/foo"
            filters:
              before:
                - "echo first before filter"
                - "echo second before filter"
              after:
                - "echo first after filter"
                - "echo second after filter"
            panes:
              - cmd: "echo 'foo'"
              - cmd: "echo 'foo again'"
                width: 50

    two-windows-with-custom-command-options:
        windows:
          - name: "foo"
            cmd_separator: "\n"
            with_env_var: false
            clear: true
            root: "/foo"
            layout: "tiled"
            panes:
                - cmd: "echo 'foo'"
                - cmd: "echo 'foo again'"
          - name: "bar"
            cmd_separator: " && "
            with_env_var: true
            root: "/bar"
            splits:
              - cmd:
                - "echo 'bar'"
                - "echo 'bar in an array'"
                target: bottom-right
              - cmd: "echo 'bar again'"
                focus: true
                width: 50

    three-windows-within-a-session:
        session:
            name: "my awesome session"
            windows:
            - name: "first window"
              panes:
                - cmd: "echo 'foo'"
            - name: "second window"
              panes:
                - cmd: "echo 'foo'"
            - name: "third window"
              panes:
                - cmd: "echo 'foo'"
    """

    teamocil_dict = {
        'two-windows': {
            'windows': [{
                'name': 'foo',
                'clear': True,
                'root': '/root',
                'layout': 'tiled',
                'panes': [
                    {'cmd': "echo 'foo'"},
                    {'cmd': "echo 'foo again'"}
                ]
            },
                {
                    'name': 'bar',
                    'root': '/bar',
                    'splits': [
                        {'cmd': [
                         "echo 'bar'",
                         "echo 'bar in an array'"
                         ],
                         'target': 'bottom-right'
                         },
                        {'cmd': "echo 'bar again'",
                         'focus': True,
                         'width': 50
                         }
                    ]

                }]
        },

        'two-windows-with-filters': {
            'windows': [{
                'name': 'foo',
                'root': '/foo',
                'filters': {
                    'before': [
                        'echo first before filter',
                        'echo second before filter'
                        ],
                    'after': [
                        'echo first after filter',
                        'echo second after filter',
                        ]
                },
                'panes': [
                    { 'cmd': "echo 'foo'" },
                    { 'cmd': "echo 'foo again'", 'width': 50 }
                ]
            }]
        },

        'two-windows-with-custom-command-options': {
            'windows': [{
                'name': 'foo',
                'cmd_separator': '\n',
                'with_env_var': False,
                'clear': True,
                'root': '/foo',
                'layout': 'tiled',
                'panes': [
                    { 'cmd': "echo 'foo'" },
                    { 'cmd': "echo 'foo again'" }
                    ]
            }, {
                'name': 'bar',
                'cmd_separator': ' && ',
                'with_env_var': True,
                'root': '/bar',
                'splits': [
                    { 'cmd': [
                        "echo 'bar'",
                        "echo 'bar in an array'"
                    ]},
                    { 'cmd': "echo 'bar again'",
                    'focus': True,
                    'width': 50
                    }
                ]
            }]
        },

        'three-windows-within-a-session': {
            'session': {
                'name': 'my awesome session',
                'windows': [
                { 'name': 'first window',
                'panes': [
                    { 'cmd': "echo 'foo'" }
                    ]
                }, {
                'name': 'second window',
                'panes': {
                    'cmd': "echo 'foo'" }
                }, {
                'name': 'third window',
                'panes': [
                    { 'cmd': "echo 'foo'" }
                ]}
                ]
            }
        }
    }

    def test_config_to_dict(self):
        self.maxDiff = None
        configparser = kaptan.Kaptan(handler='yaml')
        test_config = configparser.import_config(self.teamocil_yaml)
        yaml_to_dict = test_config.get()
        self.assertDictEqual(yaml_to_dict, self.teamocil_dict)


if __name__ == '__main__':
    unittest.main()
