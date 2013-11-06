# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

try:
    import unittest2 as unittest
except ImportError:  # Python 2.7
    import unittest

import logging

logger = logging.getLogger(__name__)


class ServerTest(unittest.TestCase):

    def test_thing(self):
        pass

if __name__ == '__main__':
    unittest.main()
