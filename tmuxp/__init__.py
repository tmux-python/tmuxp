# -*- coding: utf8 - *-
"""
    tmuxp
    ~~~~~

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""


from __future__ import absolute_import, division, print_function, with_statement

#__import__('pkg_resources').declare_namespace(__name__)

from .session import Session
from .server import Server
from .window import Window
from .pane import Pane
from .builder import Builder
from .cli import main
from . import config

from .util import TmuxObject
import logging

__version__ = '0.0.1-dev'
