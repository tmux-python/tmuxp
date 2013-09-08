# -*- coding: utf8 - *-
"""
    tmuxp
    ~~~~~

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""

__version__ = '0.01-dev'

from .session import Session
from .server import Server
from .window import Window
from .pane import Pane

from .util import live_tmux, TmuxObject

t = Server()
