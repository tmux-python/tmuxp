# -*- coding: utf-8 -*-
"""Tests for tmuxp.

tmuxp.tests
~~~~~~~~~~~

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import os

current_dir = os.path.abspath(os.path.dirname(__file__))
example_dir = os.path.abspath(os.path.join(current_dir, '..', 'examples'))
fixtures_dir = os.path.realpath(os.path.join(current_dir, 'fixtures'))
