# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import unittest
from .helpers import TmuxTestCase
from . import t

from .. import log
import logging

logger = logging.getLogger(__name__)


class ResizeTest(TmuxTestCase):

    @classmethod
    def setUpClass(cls):
        super(ResizeTest, cls).setUpClass()

    def test_window_pane(self):
        '''Pane.resize_pane()'''

        window = self.session.attached_window()

        pane1 = window.attached_pane()
        pane1_id = pane1['pane_id']
        pane1_height = pane1['pane_height']
        pane2 = window.split_window()

        pane1.resize_pane(height=20)
        self.assertNotEqual(pane1['pane_height'], pane1_height)
        self.assertEqual(int(pane1['pane_height']), 20)

        pane1.resize_pane(height=10)
        self.assertEqual(int(pane1['pane_height']), 10)
