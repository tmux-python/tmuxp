# -*- coding: utf-8 -*-
"""Test for tmuxp Pane object.

tmuxp.tests.test_pane
~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2013 Tony Narlock.
:license: BSD, see LICENSE for details

"""
from __future__ import absolute_import, division, print_function, with_statement

from . import t
from .helpers import TmuxTestCase

import logging

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

        pane1.resize_pane(height=7)
        self.assertNotEqual(pane1['pane_height'], pane1_height)
        self.assertEqual(int(pane1['pane_height']), 7)

        pane1.resize_pane(height=9)
        self.assertEqual(int(pane1['pane_height']), 9)

    def test_set_height(self):
        window = self.session.new_window(window_name='test_set_height')
        pane2 = window.split_window()
        pane1 = window.attached_pane()
        pane1_height = pane1['pane_height']

        pane1.set_height(6)
        self.assertNotEqual(pane1['pane_height'], pane1_height)
        self.assertEqual(int(pane1['pane_height']), 6)

    def test_set_width(self):
        window = self.session.new_window(window_name='test_set_width')
        pane2 = window.split_window()

        window.select_layout('main-vertical')
        pane1 = window.attached_pane()
        pane1_width = pane1['pane_width']

        pane1.set_width(25)
        self.assertNotEqual(pane1['pane_width'], pane1_width)
        self.assertEqual(int(pane1['pane_width']), 25)

        pane1.reset()
