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

from .. import exc
from ..util import has_required_tmux_version

from .helpers import TmuxTestCase

logger = logging.getLogger(__name__)


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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TmuxVersionTest))
    return suite
