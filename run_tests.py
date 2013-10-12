#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, with_statement

import unittest
import sys
import os
import subprocess
import argparse
import tmuxp.testsuite
from tmuxp.util import tmux

t = tmuxp.testsuite.t

tmux_path = sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if tmux_path not in sys.path:
    sys.path.insert(0, tmux_path)

from time import sleep
import itertools


def main(verbosity=2):

    # from tmuxp import log
    # import logging

    # logger = logging.getLogger()
    # channel = logging.StreamHandler()
    # channel.setFormatter(log.LogFormatter())
    # logger.setLevel('INFO')
    # logger.addHandler(channel)

    def has_virtualenv():
        if os.environ.get('VIRTUAL_ENV'):
            return os.environ.get('VIRTUAL_ENV')
        else:
            False

    def in_tmux():
        if os.environ.get('TMUX'):
            return True
        else:
            return False

    tmuxclient = None

    def la():
        if not in_tmux():
            shell_commands = []
            if has_virtualenv():
                shell_commands.append(
                    'source %s/bin/activate' % has_virtualenv())
            shell_commands.append('echo wat lol %s' % has_virtualenv())
            session_name = 'tmuxp'
            t.tmux('new-session', '-d', '-s', session_name)
            for shell_command in shell_commands:
                t.tmux('send-keys', '-t', session_name, shell_command, '^M')

            t.tmux('send-keys', '-R', '-t', session_name,
                   'python run_tests.py --pypid=%s' % os.getpid(), '^M')

            os.environ['pypid'] = str(os.getpid())

            # os.execl('/usr/local/bin/tmux', 'tmux', 'attach-session', '-t', session_name)
            # t.hotswap(session_name=session_name)
            def output(line):
                pass
            # tmuxclient = t.tmux('-C')
            # tmuxclient = subprocess.Popen(['tmux', '-C', '-Lhi', 'attach'],
            # stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            print(has_virtualenv())
            print(in_tmux())
            print(os.environ.get('pypid'))
            args = vars(parser.parse_args())
            if 'pypid' in args:
                print(args['pypid'])

            # todo create a hook to run after suite / loader to detach
            # and killall tmuxp + tmuxp_-prefixed sessions.
            # tmux('detach')
            # os.kill(args['pypid'], 9)
            # t.kill_server()
            suites = unittest.TestLoader().discover(
                'tmuxp.testsuite', pattern="*.py")
            result = unittest.TextTestRunner(verbosity=verbosity).run(suites)
            if result.wasSuccessful():
                sys.exit(0)
            else:
                sys.exit(1)
    session_name = 'tmuxp'
    t.tmux('new-session', '-d', '-s', session_name)
    suites = unittest.TestLoader().discover('tmuxp.testsuite', pattern="*.py")
    result = unittest.TextTestRunner(verbosity=verbosity).run(suites)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''\
        Run tests suite for tmuxp. With no arguments, runs all test suites in tmuxp.testsuite.

        Default usage:
            $ ./run_tests.py
        ''',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--visual',
        action='store_true',
        help='''\
        Run the session builder testsuite in visual mode. requires having
        tmux client in a second terminal open with:

        Terminal 1:
            $ tmux -L tmuxp_test

        Terminal 2:
            $ ./run_tests.py --visual
        '''
    )
    parser.add_argument(
        '--tests',
        nargs='*',
        default=None,
        help='''\
        Test individual, TestCase or TestSuites, or multiple. Example for test_config TestSuite:

        by TestSuite (module):
            $ ./run_tests.py tmuxp.testsuite.test_config

        by TestCase:
            $ ./run_tests.py tmuxp.testsuite.test_config.ImportExportTest
        individual tests:
            $ ./run_tests.py tmuxp.testsuite.test_config.ImportExportTest.test_export_json

        Multiple can be separated by spaces:
            $ ./run_tests.py tmuxp.testsuite.test_config.ImportExportTest.test_export_json \\
                testsuite.test_config.ImportExportTest.test_window
        '''
    )
    parser.add_argument('-l', '--log-level', dest='log_level', default='INFO',
                        help='Log level')
    parser.add_argument('-v', '--verbosity', dest='verbosity', type=int, default=2,
                        help='unittest verbosity level')
    args = parser.parse_args()

    verbosity = args.verbosity

    import logging
    logging.getLogger('tmuxp.testsuite').setLevel(args.log_level.upper())

    if 'help' in args:
        parser.print_help()
    elif 'visual' in args and args.visual:
        # todo, we can have this test build, and on completion, take the user
        # to the new session with os.exec and attach the session.
        loader = unittest.TestLoader()
        suites = loader.loadTestsFromName('tmuxp.testsuite.test_builder')
        result = unittest.TextTestRunner(verbosity=verbosity).run(suites)

        if result.wasSuccessful():
            sys.exit(0)
        else:
            sys.exit(1)
    if args.tests and len(args.tests) > int(0):
        suites = unittest.TestLoader().loadTestsFromNames(args.tests)
        result = unittest.TextTestRunner(verbosity=verbosity).run(suites)
    else:
        main(verbosity=verbosity)
