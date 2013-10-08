# -*- coding: utf8 - *-
"""
    tmuxp
    ~~~~~

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""

__version__ = '0.0.1-dev'

from .session import Session
from .server import Server
from .window import Window
from .pane import Pane
from .builder import Builder
from .config import expand_config, trickledown_config

from .util import TmuxObject

t = Server()


def main():
    print t.list_sessions()
