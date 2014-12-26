# -*- coding: utf-8 -*-
"""Tests for utility functions in tmux.

tmuxp.tests.util
~~~~~~~~~~~~~~~~

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import random
import logging
import unittest
import subprocess
import os

from .. import exc
from ..util import has_required_tmux_version, run_before_script
from ..exc import BeforeLoadScriptNotExists, BeforeLoadScriptError


from .helpers import TmuxTestCase, TestCase

logger = logging.getLogger(__name__)

current_dir = os.path.realpath(os.path.dirname(__file__))
fixtures_dir = os.path.realpath(os.path.join(current_dir, 'fixtures'))


class TmuxVersionTest(TmuxTestCase):

    """Test the :meth:`has_required_tmux_version`."""

    def test_no_arg_uses_tmux_version(self):
        result = has_required_tmux_version()
        self.assertRegexpMatches(result, r'[0-9]\.[0-9]')

    def test_ignores_letter_versions(self):
        """Ignore letters such as 1.8b.

        See ticket https://github.com/tony/tmuxp/issues/55.

        In version 0.1.7 this is adjusted to use LooseVersion, in order to
        allow letters.

        """
        result = has_required_tmux_version('1.9a')
        self.assertRegexpMatches(result, r'[0-9]\.[0-9]')

        result = has_required_tmux_version('1.8a')
        self.assertEqual(result, r'1.8')

    def test_error_version_less_1_7(self):
        with self.assertRaisesRegexp(exc.TmuxpException, 'tmuxp only supports'):
            has_required_tmux_version('1.7')

        with self.assertRaisesRegexp(exc.TmuxpException, 'tmuxp only supports'):
            has_required_tmux_version('1.6a')

        has_required_tmux_version('1.9a')


class RunBeforeScript(TestCase):

    def test_raise_BeforeLoadScriptNotExists_if_not_exists(self):
        script_file = os.path.join(fixtures_dir, 'script_noexists.sh')

        with self.assertRaises(BeforeLoadScriptNotExists):
            run_before_script(script_file)

        with self.assertRaises(OSError):
            run_before_script(script_file)

    def test_raise_BeforeLoadScriptError_if_retcode(self):
        script_file = os.path.join(fixtures_dir, 'script_failed.sh')

        with self.assertRaises(BeforeLoadScriptError):
            run_before_script(script_file)

    def test_return_stdout_if_ok(self):
        script_file = os.path.join(fixtures_dir, 'script_complete.sh')

        run_before_script(script_file)


class BeforeLoadScriptErrorTestCase(TestCase):

    def test_returncode(self):
        script_file = os.path.join(fixtures_dir, 'script_failed.sh')

        with self.assertRaisesRegexp(exc.BeforeLoadScriptError, "113"):
            run_before_script(script_file)

    def test_returns_stderr_messages(self):
        script_file = os.path.join(fixtures_dir, 'script_failed.sh')

        with self.assertRaisesRegexp(exc.BeforeLoadScriptError, "failed with returncode"):
            run_before_script(script_file)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BeforeLoadScriptErrorTestCase))
    suite.addTest(unittest.makeSuite(RunBeforeScript))
    suite.addTest(unittest.makeSuite(TmuxVersionTest))
    return suite
