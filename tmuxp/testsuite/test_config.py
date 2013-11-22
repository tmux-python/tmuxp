# -*- coding: utf-8 -*-
"""Test for tmuxp configuration import, inlining, expanding and export.

tmuxp.tests.test_config
~~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2013 Tony Narlock.
:license: BSD, see LICENSE for details

"""

from __future__ import absolute_import, division, print_function, with_statement

import os
import shutil
import tempfile
import kaptan
from .. import config, exc
from ..util import tmux
from .helpers import TestCase

import logging

logger = logging.getLogger(__name__)
TMUXP_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')
current_dir = os.path.abspath(os.path.dirname(__file__))
example_dir = os.path.abspath(os.path.join(
    current_dir, '..', '..', 'examples'))


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
                },  {
                    'shell_command': ['cowsay "hey"']
                },
            ],
            'layout': 'main-verticle'
        },
        {
            'window_name': 'logging',
            'panes': [{
                'shell_command': ['tail -F /var/log/syslog'],
                'start_directory':'/var/log'
            }]
        },
        {
            'options': {
                'automatic_rename': True,
            },
            'panes': [
                {'shell_command': ['htop']}
            ]
        }
    ]
}


class ImportExportTest(TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(suffix='tmuxp')

    def tearDown(self):
        if os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
        logging.debug('wiped %s' % TMUXP_DIR)

    def test_export_json(self):
        json_config_file = os.path.join(self.tmp_dir, 'config.json')

        configparser = kaptan.Kaptan()
        sampleconfig = config.inline(sampleconfigdict)
        configparser.import_config(sampleconfigdict)

        json_config_data = configparser.export('json', indent=2)

        with open(json_config_file, 'w') as buf:
            buf.write(json_config_data)

        new_config = kaptan.Kaptan()
        new_config_data = new_config.import_config(json_config_file).get()
        self.assertDictEqual(sampleconfigdict, new_config_data)

    def test_export_yaml(self):
        yaml_config_file = os.path.join(self.tmp_dir, 'config.yaml')

        configparser = kaptan.Kaptan()
        sampleconfig = config.inline(sampleconfigdict)
        configparser.import_config(sampleconfig)

        yaml_config_data = configparser.export(
            'yaml', indent=2, default_flow_style=False)

        with open(yaml_config_file, 'w') as buf:
            buf.write(yaml_config_data)

        new_config = kaptan.Kaptan()
        new_config_data = new_config.import_config(yaml_config_file).get()
        self.assertDictEqual(sampleconfigdict, new_config_data)

    def test_scan_config(self):
        configs = []

        garbage_file = os.path.join(self.tmp_dir, 'config.psd')
        with open(garbage_file, 'w') as buf:
            buf.write('wat')

        if os.path.exists(self.tmp_dir):
            for r, d, f in os.walk(self.tmp_dir):
                for filela in (
                    x for x in f if x.endswith(('.json', '.ini', 'yaml'))
                ):
                    configs.append(os.path.join(
                        self.tmp_dir, filela))

        files = 0
        if os.path.exists(os.path.join(self.tmp_dir, 'config.json')):
            files += 1
            self.assertIn(os.path.join(
                self.tmp_dir, 'config.json'), configs)

        if os.path.exists(os.path.join(self.tmp_dir, 'config.yaml')):
            files += 1
            self.assertIn(os.path.join(
                self.tmp_dir, 'config.yaml'), configs)

        if os.path.exists(os.path.join(self.tmp_dir, 'config.ini')):
            files += 1
            self.assertIn(os.path.join(self.tmp_dir, 'config.ini'), configs)

        self.assertEqual(len(configs), files)


class ExpandTest(TestCase):

    """Assume configuration has been imported into a python dict correctly."""

    before_config = {
        'session_name': 'sampleconfig',
        'start_directory': '~',
        'windows': [
            {
                'window_name': 'editor',
                'panes': [
                    {
                        'shell_command': [
                            'vim',
                            'top'
                        ]
                    },
                    {
                        'shell_command': ['vim'],
                    },
                    {
                        'shell_command': 'cowsay "hey"'
                    }
                ],
                'layout': 'main-verticle'
            },
            {
                'window_name': 'logging',
                'panes': [
                    {
                        'shell_command': ['tail -F /var/log/syslog'],
                    }
                ]
            },
            {
                'start_directory': '/var/log',
                'options': {'automatic_rename': True, },
                'panes': [
                    {
                        'shell_command': 'htop'
                    },
                    'vim',
                ]
            },
            {
                'start_directory': './',
                'panes': [
                    'pwd'
                ]
            },
            {
                'start_directory': './asdf/',
                'panes': [
                    'pwd'
                ]
            },
            {
                'start_directory': '../',
                'panes': [
                    'pwd'
                ]
            },
            {
                'panes': [
                    'top'
                ]
            }
        ]
    }

    after_config = {
        'session_name': 'sampleconfig',
        'start_directory': '~',
        'windows': [
            {
                'window_name': 'editor',
                'panes': [
                    {
                        'shell_command': ['vim', 'top'],
                    },
                    {
                        'shell_command': ['vim'],
                    },
                    {
                        'shell_command': ['cowsay "hey"']
                    },
                ],
                'layout': 'main-verticle'
            },
            {
                'window_name': 'logging',
                'panes': [
                    {
                        'shell_command': ['tail -F /var/log/syslog'],
                    }
                ]
            },
            {
                'start_directory': '/var/log',
                'options': {'automatic_rename': True},
                'panes': [
                    {'shell_command': ['htop']},
                    {'shell_command': ['vim']}
                ]
            },
            {
                'start_directory': os.path.abspath('./'),
                'panes': [
                    {'shell_command': ['pwd']}
                ]
            },
            {
                'start_directory': os.path.abspath('./asdf/'),
                'panes': [
                    {'shell_command': ['pwd']}
                ]
            },
            {
                'start_directory': os.path.abspath('../'),
                'panes': [
                    {'shell_command': ['pwd']}
                ]
            },

            {
                'panes': [
                    {'shell_command': ['top']}
                ]
            }
        ]
    }

    def test_config(self):
        """Expand shell commands from string to list."""
        self.maxDiff = None
        test_config = config.expand(self.before_config)
        self.assertDictEqual(test_config, self.after_config)


class InlineTest(TestCase):

    """Tests for :meth:`config.inline()`."""

    before_config = {
        'session_name': 'sampleconfig',
        'start_directory': '~',
        'windows': [
            {
                'shell_command': ['top'],
                'window_name': 'editor',
                'panes': [
                    {
                        'shell_command': ['vim'],
                    },  {
                        'shell_command': ['cowsay "hey"']
                    },
                ],
                'layout': 'main-verticle'
            },
            {
                'window_name': 'logging',
                'panes': [
                    {
                        'shell_command': ['tail -F /var/log/syslog'],
                    }
                ]
            },
            {
                'options': {'automatic_rename': True, },
                'panes': [
                    {'shell_command': ['htop']}
                ]
            }
        ]
    }

    after_config = {
        'session_name': 'sampleconfig',
        'start_directory': '~',
        'windows': [
            {
                'shell_command': 'top',
                'window_name': 'editor',
                'panes': [
                    'vim',
                    'cowsay "hey"'
                ],
                'layout': 'main-verticle'
            },
            {
                'window_name': 'logging',
                'panes': [
                    'tail -F /var/log/syslog',
                ]
            },
            {
                'options': {
                    'automatic_rename': True,
                },
                'panes': [
                    'htop'
                ]
            },

        ]
    }

    def test_config(self):
        """:meth:`config.inline()` shell commands list to string."""

        self.maxDiff = None
        test_config = config.inline(self.before_config)
        self.assertDictEqual(test_config, self.after_config)


class InheritanceTest(TestCase):

    """Test config inheritance for the nested 'start_command'."""

    config_before = {
        'session_name': 'sampleconfig',
        'start_directory': '/',
        'windows': [
            {
                'window_name': 'editor',
                'start_directory': '~',
                'panes': [
                    {
                        'shell_command': ['vim'],
                    },
                    {
                        'shell_command': ['cowsay "hey"']
                    },
                ],
                'layout': 'main-verticle'
            },
            {
                'window_name': 'logging',
                'panes': [
                    {
                        'shell_command': ['tail -F /var/log/syslog'],
                    }
                ]
            },
            {
                'window_name': 'shufu',
                'panes': [
                    {
                        'shell_command': ['htop'],
                    }
                ]
            },
            {
                'options': {
                    'automatic_rename': True,
                },
                'panes': [
                    {
                        'shell_command': ['htop']
                    }
                ]
            }
        ]
    }

    config_after = {
        'session_name': 'sampleconfig',
        'start_directory': '/',
        'windows': [
            {
                'window_name': 'editor',
                'start_directory': '~',
                'panes': [
                    {
                        'shell_command': ['vim'],
                    },  {
                        'shell_command': ['cowsay "hey"'],
                    },
                ],
                'layout': 'main-verticle'
            },
            {
                'window_name': 'logging',
                'panes': [
                    {
                        'shell_command': ['tail -F /var/log/syslog'],
                    }
                ]
            },
            {
                'window_name': 'shufu',
                'panes': [
                    {
                        'shell_command': ['htop'],
                    }
                ]
            },
            {
                'options': {'automatic_rename': True, },
                'panes': [
                    {
                        'shell_command': ['htop'],
                    }
                ]
            }
        ]
    }

    def test_start_directory(self):
        config = self.config_before

        if 'start_directory' in config:
            session_start_directory = config['start_directory']
        else:
            session_start_directory = None

        for windowconfitem in config['windows']:
            window_start_directory = None
            if 'start_directory' in windowconfitem:
                window_start_directory = windowconfitem['start_directory']
            elif session_start_directory:
                window_start_directory = session_start_directory

            for paneconfitem in windowconfitem['panes']:
                # if 'start_directory' in paneconfitem:
                    # pane_start_directory = paneconfitem['start_directory']
                # elif window_start_directory:
                    # paneconfitem['start_directory'] = window_start_directory
                # elif session_start_directory:
                    # paneconfitem['start_directory'] = session_start_directory
                pass

        self.maxDiff = None
        self.assertDictEqual(config, self.config_after)


class ShellCommandBeforeTest(TestCase):

    """Config inheritance for the nested 'start_command'."""

    config_unexpanded = {  # shell_command_before is string in some areas
        'session_name': 'sampleconfig',
        'start_directory': '/',
        'windows': [
            {
                'window_name': 'editor',
                'start_directory': '~',
                'shell_command_before': 'source .env/bin/activate',
                'panes': [
                    {
                        'shell_command': ['vim'],
                    },
                    {
                        'shell_command_before': ['rbenv local 2.0.0-p0'],
                        'shell_command': ['cowsay "hey"']
                    },
                ],
                'layout': 'main-verticle'
            },
            {
                'shell_command_before': 'rbenv local 2.0.0-p0',
                'window_name': 'logging',
                'panes': [
                    {
                        'shell_command': ['tail -F /var/log/syslog'],
                    },
                    {
                    }
                ]
            },
            {
                'window_name': 'shufu',
                'panes': [
                    {
                        'shell_command_before': ['rbenv local 2.0.0-p0'],
                        'shell_command': ['htop'],
                    }
                ]
            },
            {
                'options': {'automatic_rename': True, },
                'panes': [
                    {'shell_command': ['htop']}
                ]
            },
            {
                'panes': ['top']
            }
        ]
    }

    config_expanded = {  # shell_command_before is string in some areas
        'session_name': 'sampleconfig',
        'start_directory': '/',
        'windows': [
            {
                'window_name': 'editor',
                'start_directory': '~',
                'shell_command_before': ['source .env/bin/activate'],
                'panes': [
                    {
                        'shell_command': ['vim'],
                    },
                    {
                        'shell_command_before': ['rbenv local 2.0.0-p0'],
                        'shell_command': ['cowsay "hey"']
                    },
                ],
                'layout': 'main-verticle'
            },
            {
                'shell_command_before': ['rbenv local 2.0.0-p0'],
                'window_name': 'logging',
                'panes': [
                    {
                        'shell_command': ['tail -F /var/log/syslog'],
                    },
                    {
                        'shell_command': []
                    }
                ]
            },
            {
                'window_name': 'shufu',
                'panes': [
                    {
                        'shell_command_before': ['rbenv local 2.0.0-p0'],
                        'shell_command': ['htop'],
                    }
                ]
            },
            {
                'options': {'automatic_rename': True, },
                'panes': [
                    {'shell_command': ['htop']}
                ]
            },
            {
                'panes': [{
                    'shell_command': ['top']
                }]
            },
        ]
    }

    config_after = {  # shell_command_before is string in some areas
        'session_name': 'sampleconfig',
        'start_directory': '/',
        'windows': [
            {
                'window_name': 'editor',
                'start_directory': '~',
                'shell_command_before': ['source .env/bin/activate'],
                'panes': [
                    {
                        'shell_command': ['source .env/bin/activate', 'vim'],
                    },
                    {
                        'shell_command_before': ['rbenv local 2.0.0-p0'],
                        'shell_command': [
                            'source .env/bin/activate',
                            'rbenv local 2.0.0-p0', 'cowsay "hey"'
                        ]
                    },
                ],
                'layout': 'main-verticle'
            },
            {
                'shell_command_before': ['rbenv local 2.0.0-p0'],
                'start_directory': '/',
                'window_name': 'logging',
                'panes': [
                    {
                        'shell_command': [
                            'rbenv local 2.0.0-p0',
                            'tail -F /var/log/syslog'
                        ],
                    },
                    {
                        'shell_command': ['rbenv local 2.0.0-p0']
                    }
                ]
            },
            {
                'start_directory': '/',
                'window_name': 'shufu',
                'panes': [
                    {
                        'shell_command_before': ['rbenv local 2.0.0-p0'],
                        'shell_command': ['rbenv local 2.0.0-p0', 'htop'],
                    }
                ]
            },
            {
                'start_directory': '/',
                'options': {'automatic_rename': True, },
                'panes': [
                    {
                        'shell_command': ['htop']
                    }
                ]
            },
            {
                'start_directory': '/',
                'panes': [
                    {
                        'shell_command': ['top']
                    }
                ]
            }
        ]
    }

    def test_shell_command_before(self):
        self.maxDiff = None
        test_config = self.config_unexpanded
        test_config = config.expand(test_config)

        self.assertDictEqual(test_config, self.config_expanded)

        test_config = config.trickle(test_config)
        self.maxDiff = None
        self.assertDictEqual(test_config, self.config_after)


class TrickleRelativeStartDirectory(TestCase):

    config_expanded = {  # shell_command_before is string in some areas
        'session_name': 'sampleconfig',
        'start_directory': '/var',
        'windows': [
            {
                'window_name': 'editor',
                'start_directory': 'log',
                'panes': [
                    {
                        'shell_command': ['vim'],
                    },
                    {
                        'shell_command': ['cowsay "hey"']
                    },
                ],
                'layout': 'main-verticle'
            },
            {
                'window_name': 'logging',
                'start_directory': '~',
                'panes': [
                    {
                        'shell_command': ['tail -F /var/log/syslog'],
                    },
                    {
                        'shell_command': []
                    }
                ]
            },
        ]
    }

    config_after = {  # shell_command_before is string in some areas
        'session_name': 'sampleconfig',
        'start_directory': '/var',
        'windows': [
            {
                'window_name': 'editor',
                'start_directory': '/var/log',
                'panes': [
                    {
                        'shell_command': ['vim'],
                    },
                    {
                        'shell_command': [
                            'cowsay "hey"'
                        ]
                    },
                ],
                'layout': 'main-verticle'
            },
            {
                'start_directory': '~',
                'window_name': 'logging',
                'panes': [
                    {
                        'shell_command': ['tail -F /var/log/syslog'],
                    },
                    {
                        'shell_command': []
                    }
                ]
            },
        ]
    }

    def test_shell_command_before(self):

        test_config = config.trickle(self.config_expanded)
        self.assertDictEqual(test_config, self.config_after)


class ConfigBlankPanes(TestCase):

    yaml_config_file = os.path.join(example_dir, 'blank-panes.yaml')

    expanded_config = {
        'session_name': 'Blank pane test',
        'windows': [
            {
                'window_name': 'Blank pane test',
                'layout': 'tiled',
                'panes': [
                    {
                        'shell_command': [],
                    },
                    {
                        'shell_command': [],
                    },
                    {
                        'shell_command': [],
                    },
                    {
                        'shell_command': [],
                    },
                    {
                        'shell_command': [],
                    },
                    {
                        'shell_command': [],
                    }
                ]
            },
            {
                'window_name': 'Empty string (return)',
                'panes': [
                    {
                        'shell_command': [
                            ''
                        ],
                    },
                    {
                        'shell_command': [
                            ''
                        ],
                    },
                    {
                        'shell_command': [
                            ''
                        ],
                    }
                ]
            }
        ]
    }

    def test_expands_blank(self):
        """Expand blank config into full form.

        Handle ``NoneType`` and 'blank'::

        # nothing, None, 'blank'
        'panes': [
            None,
            'blank'
        ]

        # should be blank
        'panes': [
            'shell_command': []
        ]

        Blank strings::

            panes: [
                ''
            ]

            # should output to:
            panes:
                'shell_command': ['']

        """

        self.maxDiff = None

        test_config = kaptan.Kaptan().import_config(
            self.yaml_config_file).get()

        self.assertDictEqual(
            config.expand(test_config),
            self.expanded_config
        )


class ConfigConsistency(TestCase):

    delete_this = """
    session_name: sampleconfig
    start_directory: '~'
    windows:
    - layout: main-vertical
    panes:
    - shell_command:
        - vim
        start_directory: '~'
    - shell_command:
        - cowsay "hey"
    window_name: editor
    - panes:
    - shell_command:
        - tail -F /var/log/syslog
        start_directory: /var/log
    window_name: logging
    - automatic_rename: true
    panes:
    - shell_command:
        - htop
    """

    def test_no_session_name(self):
        yaml_config = """
        - window_name: editor
          panes:
          shell_command:
            - tail -F /var/log/syslog
          start_directory: /var/log
        - window_name: logging
          automatic_rename: true
          panes:
          - shell_command:
            - htop
        """

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(yaml_config).get()

        with self.assertRaisesRegexp(
            exc.ConfigError, 'requires "session_name"'
        ):
            config.validate_schema(sconfig)

    def test_no_windows(self):
        yaml_config = """
        session_name: test session
        """

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(yaml_config).get()

        with self.assertRaisesRegexp(exc.ConfigError, 'list of "windows"'):
            config.validate_schema(sconfig)

    def test_no_window_name(self):
        yaml_config = """
        session_name: test session
        windows:
        - window_name: editor
          panes:
          shell_command:
            - tail -F /var/log/syslog
          start_directory: /var/log
        - automatic_rename: true
          panes:
          - shell_command:
            - htop
        """

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(yaml_config).get()

        with self.assertRaisesRegexp(exc.ConfigError, 'missing "window_name"'):
            config.validate_schema(sconfig)
