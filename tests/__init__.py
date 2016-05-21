# -*- coding: utf-8 -*-
"""Tests for tmuxp.

tmuxp.tests
~~~~~~~~~~~

"""
from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import logging
import pkgutil
import sys

from tmuxp import log
from tmuxp._compat import string_types, PY2, reraise
from tmuxp.server import Server

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

t = Server()
t.socket_name = 'tmuxp_test'

from . import helpers  # NOQA
