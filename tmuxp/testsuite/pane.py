# -*- coding: utf-8 -*-
"""Test for tmuxp Pane object.

tmuxp.tests.pane
~~~~~~~~~~~~~~~~

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import unittest
import logging

from . import t
from .helpers import TmuxTestCase

logger = logging.getLogger(__name__)


class ResizeTest(TmuxTestCase):

    def test_resize_pane(self):
        """ Test Pane.resize_pane(). """

        window = self.session.attached_window()
        window.rename_window('test_resize_pane')

        pane1 = window.attached_pane()
        pane1_id = pane1['pane_id']
        pane1_height = pane1['pane_height']
        pane2 = window.split_window()

        pane1.resize_pane(height=4)
        self.assertNotEqual(pane1['pane_height'], pane1_height)
        self.assertEqual(int(pane1['pane_height']), 4)

        pane1.resize_pane(height=3)
        self.assertEqual(int(pane1['pane_height']), 3)

    def test_set_height(self):
        window = self.session.new_window(window_name='test_set_height')
        pane2 = window.split_window()
        pane1 = window.attached_pane()
        pane1_height = pane1['pane_height']

        pane1.set_height(2)
        self.assertNotEqual(pane1['pane_height'], pane1_height)
        self.assertEqual(int(pane1['pane_height']), 2)

    def test_set_width(self):
        window = self.session.new_window(window_name='test_set_width')
        pane2 = window.split_window()

        window.select_layout('main-vertical')
        pane1 = window.attached_pane()
        pane1_width = pane1['pane_width']

        pane1.set_width(10)
        self.assertNotEqual(pane1['pane_width'], pane1_width)
        self.assertEqual(int(pane1['pane_width']), 10)

        pane1.reset()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ResizeTest))
    return suite
