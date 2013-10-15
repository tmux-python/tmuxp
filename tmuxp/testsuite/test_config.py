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


class ImportExportTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TMUXP_DIR):
            os.makedirs(TMUXP_DIR)

    def test_export_json(self):
        json_config_file = os.path.join(TMUXP_DIR, 'config.json')

        configparser = kaptan.Kaptan()
        sampleconfig = config.inline(sampleconfigdict)
        configparser.import_config(sampleconfigdict)

        json_config_data = configparser.export('json', indent=2)

        buf = open(json_config_file, 'w')
        buf.write(json_config_data)
        buf.close()

        new_config = kaptan.Kaptan()
        new_config_data = new_config.import_config(json_config_file).get()
        self.assertDictEqual(sampleconfigdict, new_config_data)

    def test_export_yaml(self):
        yaml_config_file = os.path.join(TMUXP_DIR, 'config.yaml')

        configparser = kaptan.Kaptan()
        sampleconfig = config.inline(sampleconfigdict)
        configparser.import_config(sampleconfig)

        yaml_config_data = configparser.export('yaml', indent=2, default_flow_style=False)

        buf = open(yaml_config_file, 'w')
        buf.write(yaml_config_data)
        buf.close()

        new_config = kaptan.Kaptan()
        new_config_data = new_config.import_config(yaml_config_file).get()
        self.assertDictEqual(sampleconfigdict, new_config_data)

    def test_scan_config(self):
        configs = []

        garbage_file = os.path.join(TMUXP_DIR, 'config.psd')
        buf = open(garbage_file, 'w')
        buf.write('wat')
        buf.close()

        if os.path.exists(TMUXP_DIR):
            for r, d, f in os.walk(TMUXP_DIR):
                for filela in (x for x in f if x.endswith(('.json', '.ini', 'yaml'))):
                    configs.append(os.path.join(
                        TMUXP_DIR, filela))

        files = 0
        if os.path.exists(os.path.join(TMUXP_DIR, 'config.json')):
            files += 1
            self.assertIn(os.path.join(
                TMUXP_DIR, 'config.json'), configs)

        if os.path.exists(os.path.join(TMUXP_DIR, 'config.yaml')):
            files += 1
            self.assertIn(os.path.join(
                TMUXP_DIR, 'config.yaml'), configs)

        if os.path.exists(os.path.join(TMUXP_DIR, 'config.ini')):
            files += 1
            self.assertIn(os.path.join(TMUXP_DIR, 'config.ini'), configs)

        self.assertEqual(len(configs), files)

    @classmethod
    def tearDownClass(cls):
        #if os.path.isdir(TMUXP_DIR):
        #    shutil.rmtree(TMUXP_DIR)
        logging.debug('wiped %s' % TMUXP_DIR)


class ExpandTest(unittest.TestCase):

    '''
    assumes the configuration has been imported into a python dict correctly.
    '''

    before_config = {
        'session_name': 'sampleconfig',
        'start_directory': '~',
        'windows': [{
            'shell_command': 'top',
            'window_name': 'editor',
            'panes': [
                {
                    'start_directory': '~', 'shell_command': ['vim'],
                    },  {
                    'shell_command': 'cowsay "hey"'
                },
            ],
            'layout': 'main-verticle'},
            {
                'window_name': 'logging',
                'panes': [
                    {'shell_command': ['tail -F /var/log/syslog'],
                     'start_directory':'/var/log'}
                ]
            },
            {
                'automatic_rename': True,
                'panes': [
                    {'shell_command': 'htop'},
                    'vim',
                ]
            }]
    }

    after_config = {
        'session_name': 'sampleconfig',
        'start_directory': '~',
        'windows': [{
            'shell_command': ['top'],
            'window_name': 'editor',
            'panes': [
                {
                    'start_directory': '~', 'shell_command': ['vim'],
                    },  {
                    'shell_command': ['cowsay "hey"']
                },
            ],
            'layout': 'main-verticle'},
            {
                'window_name': 'logging',
                'panes': [
                    {'shell_command': ['tail -F /var/log/syslog'],
                     'start_directory':'/var/log'}
                ]
            },
            {
                'automatic_rename': True,
                'panes': [
                    {'shell_command': ['htop']},
                    {'shell_command': ['vim']}
                ]
            }]
    }

    def test_config(self):
        '''
        expands shell commands from string to list
        '''
        test_config = config.expand(self.before_config)
        self.assertDictEqual(test_config, self.after_config)


class InlineTest(unittest.TestCase):
    '''tests for :meth:`config.inline()`.
    '''

    before_config = {
        'session_name': 'sampleconfig',
        'start_directory': '~',
        'windows': [{
            'shell_command': ['top'],
            'window_name': 'editor',
            'panes': [
                {
                    'start_directory': '~', 'shell_command': ['vim'],
                    },  {
                    'shell_command': ['cowsay "hey"']
                },
            ],
            'layout': 'main-verticle'},
            {
                'window_name': 'logging',
                'panes': [
                    {'shell_command': ['tail -F /var/log/syslog'],
                     'start_directory':'/var/log'}
                ]
            },
            {
                'automatic_rename': True,
                'panes': [
                    {'shell_command': ['htop']}
                ]
            }]
    }

    after_config = {
        'session_name': 'sampleconfig',
        'start_directory': '~',
        'windows': [{
            'shell_command': 'top',
            'window_name': 'editor',
            'panes': [
                {
                    'start_directory': '~', 'shell_command': 'vim',
                    },  {
                    'shell_command': 'cowsay "hey"'
                },
            ],
            'layout': 'main-verticle'},
            {
                'window_name': 'logging',
                'panes': [
                    {'shell_command': 'tail -F /var/log/syslog',
                     'start_directory':'/var/log'}
                ]
            },
            {
                'automatic_rename': True,
                'panes': [
                    {'shell_command': 'htop'}
                ]
            }]
    }

    def test_config(self):
        '''
        config.inline() inlines shell commands from list to string where applicable
        '''
        self.maxDiff = None
        test_config = config.inline(self.before_config)
        self.assertDictEqual(test_config, self.after_config)


class InheritanceTest(unittest.TestCase):

    '''
    test config inheritance for the nested 'start_command'

    format for tests will be
    '''

    config_before = {
        'session_name': 'sampleconfig',
        'start_directory': '/',
        'windows': [{
            'window_name': 'editor',
            'start_directory': '~',
            'panes': [
                {
                    'start_directory': '~', 'shell_command': ['vim'],
                    },  {
                    'shell_command': ['cowsay "hey"']
                },
            ],
            'layout': 'main-verticle'},
            {
                'window_name': 'logging',
                'panes': [
                    {'shell_command': ['tail -F /var/log/syslog'],
                        'start_directory':'/var/log'}
                ]
            },
            {
                'window_name': 'shufu',
                'panes': [
                    {'shell_command': ['htop'], 'start_directory': '/etc/'}
                ]
            },
            {
                'automatic_rename': True,
                'panes': [
                    {'shell_command': ['htop']}
                ]
            }]
    }

    config_after = {
        'session_name': 'sampleconfig',
        'start_directory': '/',
        'windows': [{
            'window_name': 'editor',
            'start_directory': '~',
            'panes': [
                {
                    'start_directory': '~', 'shell_command': ['vim'],
                    },  {
                    'shell_command': ['cowsay "hey"'], 'start_directory': '~',
                },
            ],
            'layout': 'main-verticle'},
            {
                'window_name': 'logging',
                'panes': [
                    {'shell_command': ['tail -F /var/log/syslog'],
                        'start_directory':'/var/log'}
                ]
            },
            {
                'window_name': 'shufu',
                'panes': [
                    {'shell_command': ['htop'], 'start_directory': '/etc/'}
                ]
            },
            {
                'automatic_rename': True,
                'panes': [
                    {'shell_command': ['htop'], 'start_directory':'/'}
                ]
            }]
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
                if 'start_directory' in paneconfitem:
                    pane_start_directory = paneconfitem['start_directory']
                elif window_start_directory:
                    paneconfitem['start_directory'] = window_start_directory
                elif session_start_directory:
                    paneconfitem['start_directory'] = session_start_directory

        self.maxDiff = None
        self.assertDictEqual(config, self.config_after)


class ShellCommandBeforeTest(unittest.TestCase):

    '''
    test config inheritance for the nested 'start_command'

    format for tests will be pre
    '''

    config_unexpanded = {  # shell_command_before is string in some areas
        'session_name': 'sampleconfig',
        'start_directory': '/',
        'windows': [{
            'window_name': 'editor',
            'start_directory': '~',
            'shell_command_before': 'source .env/bin/activate',
            'panes': [
                {
                    'start_directory': '~', 'shell_command': ['vim'],
                    },  {
                    'shell_command_before': ['rbenv local 2.0.0-p0'], 'shell_command': ['cowsay "hey"']
                },
            ],
            'layout': 'main-verticle'},
            {
                'shell_command_before': 'rbenv local 2.0.0-p0',
                'window_name': 'logging',
                'panes': [
                    {'shell_command': ['tail -F /var/log/syslog'],
                        'start_directory':'/var/log'},
                    {
                        'start_directory': '/var/log'}
                ]
            },
            {
                'window_name': 'shufu',
                'panes': [
                    {
                        'shell_command_before': ['rbenv local 2.0.0-p0'],
                        'shell_command': ['htop'], 'start_directory': '/etc/'}
                ]
            },
            {
                'automatic_rename': True,
                'panes': [
                    {'shell_command': ['htop']}
                ]
            }]
    }

    config_expanded = {  # shell_command_before is string in some areas
        'session_name': 'sampleconfig',
        'start_directory': '/',
        'windows': [{
            'window_name': 'editor',
            'start_directory': '~',
            'shell_command_before': ['source .env/bin/activate'],
            'panes': [
                {
                    'start_directory': '~', 'shell_command': ['vim'],
                    },  {
                    'shell_command_before': ['rbenv local 2.0.0-p0'], 'shell_command': ['cowsay "hey"']
                },
            ],
            'layout': 'main-verticle'},
            {
                'shell_command_before': ['rbenv local 2.0.0-p0'],
                'window_name': 'logging',
                'panes': [
                    {'shell_command': ['tail -F /var/log/syslog'],
                        'start_directory':'/var/log'},
                    {
                        'start_directory': '/var/log'}
                ]
            },
            {
                'window_name': 'shufu',
                'panes': [
                    {
                        'shell_command_before': ['rbenv local 2.0.0-p0'],
                        'shell_command': ['htop'], 'start_directory': '/etc/'}
                ]
            },
            {
                'automatic_rename': True,
                'panes': [
                    {'shell_command': ['htop']}
                ]
            }]
    }

    config_after = {  # shell_command_before is string in some areas
        'session_name': 'sampleconfig',
        'start_directory': '/',
        'windows': [{
            'window_name': 'editor',
            'start_directory': '~',
            'shell_command_before': ['source .env/bin/activate'],
            'panes': [
                {
                    'start_directory': '~', 'shell_command': ['source .env/bin/activate', 'vim'],
                    },  {
                    'shell_command_before': ['rbenv local 2.0.0-p0'], 'shell_command': ['source .env/bin/activate', 'rbenv local 2.0.0-p0', 'cowsay "hey"']
                },
            ],
            'layout': 'main-verticle'},
            {
                'shell_command_before': ['rbenv local 2.0.0-p0'],
                'window_name': 'logging',
                'panes': [
                    {'shell_command': ['rbenv local 2.0.0-p0', 'tail -F /var/log/syslog'],
                        'start_directory':'/var/log'},
                    {
                        'start_directory': '/var/log', 'shell_command': ['rbenv local 2.0.0-p0']}
                ]
            },
            {
                'window_name': 'shufu',
                'panes': [
                    {
                        'shell_command_before': ['rbenv local 2.0.0-p0'],
                        'shell_command': ['rbenv local 2.0.0-p0', 'htop'], 'start_directory': '/etc/'}
                ]
            },
            {
                'automatic_rename': True,
                'panes': [
                    {'shell_command': ['htop']}
                ]
            }]
    }

    def test_shell_command_before(self):
        test_config = self.config_unexpanded
        test_config = config.expand(test_config)

        self.assertDictEqual(test_config, self.config_expanded)

        test_config = config.trickle(test_config)
        self.maxDiff = None
        self.assertDictEqual(test_config, self.config_after)


class ConfigConsistency(unittest.TestCase):

    delete_this = '''
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
    '''

    def test_no_session_name(self):
        yaml_config = '''
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
        '''

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(yaml_config).get()

        with self.assertRaisesRegexp(exc.ConfigError, 'requires "session_name"'):
            config.check_consistency(sconfig)

    def test_no_windows(self):
        yaml_config = '''
        session_name: test session
        '''

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(yaml_config).get()

        with self.assertRaisesRegexp(exc.ConfigError, 'list of "windows"'):
            config.check_consistency(sconfig)

    def test_no_window_name(self):
        yaml_config = '''
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
        '''

        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(yaml_config).get()

        with self.assertRaisesRegexp(exc.ConfigError, 'missing "window_name"'):
            config.check_consistency(sconfig)




if __name__ == '__main__':
    unittest.main()
