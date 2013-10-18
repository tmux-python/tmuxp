# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import unittest
import random
from .. import Pane, Window, Session
from .helpers import TmuxTestCase, t

from .. import log
import logging

logger = logging.getLogger(__name__)


class ServerTest(unittest.TestCase):

    def test_thing(self):
        pass

if __name__ == '__main__':
    unittest.main()
