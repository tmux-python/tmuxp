# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import unittest
from ..exc import TmuxSessionNotFound
from .helpers import TmuxTestCase
from . import t

from .. import log
import logging

logger = logging.getLogger(__name__)


class ResizeTest(TmuxTestCase):

    @classmethod
    def setUpClass(cls):
        super(ResizeTest, cls).setUpClass()

    def test_window_resize(self):
        '''Window.resize_window()'''

        window = self.session.attached_window()

        logger.error(window.attached_pane()._TMUX)
