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


def main(verbosity=2, failfast=False):

    session_name = 'tmuxp'
    t.tmux('new-session', '-d', '-s', session_name)
    suites = unittest.TestLoader().discover('tmuxp.testsuite', pattern="*.py")
    result = unittest.TextTestRunner(
        verbosity=verbosity, failfast=failfast).run(suites)
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
            $ ./run_tests.py test_config

        by TestCase:
            $ ./run_tests.py test_config.ImportExportTest
        individual tests:
            $ ./run_tests.py test_config.ImportExportTest.test_export_json

        Multiple can be separated by spaces:
            $ ./run_tests.py test_config.ImportExportTest.test_export_json \\
                test_config.ImportExportTest.test_window

        ./run_tests will automatically assume the package namespace ``tmuxp.testsuite``.

            $ ./run_tests.py test_config.ImportExportTest

        is the same as:

            $ ./run_tests.py tmuxp.testsuite.test_config.ImportExportTest
        '''
    )
    parser.add_argument('-l', '--log-level', dest='log_level', default='INFO',
                        help='Log level')
    parser.add_argument(
        '-v', '--verbosity', dest='verbosity', type=int, default=2,
        help='unittest verbosity level')
    parser.add_argument(
        '-F', '--failfast', dest='failfast', action='store_true',

        help='Stop on first test failure. failfast=True')
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
        result = unittest.TextTestRunner(
            verbosity=verbosity, failfast=args.failfast).run(suites)

        if result.wasSuccessful():
            sys.exit(0)
        else:
            sys.exit(1)
    if args.tests and len(args.tests) > int(0):
        for arg in args.tests:
            if not arg.startswith('tmuxp.testsuite'):
                loc = args.tests.index(arg)
                args.tests[loc] = 'tmuxp.testsuite.%s' % arg
        suites = unittest.TestLoader().loadTestsFromNames(args.tests)
        result = unittest.TextTestRunner(
            verbosity=verbosity, failfast=args.failfast).run(suites)
    else:
        main(verbosity=verbosity, failfast=args.failfast)
