# -*- coding: utf8 - *-
"""
    tmuxwrapper
    ~~~~~~~~~~~

    :copyright: Copyright 2013 Tony Narlock <tony@git-pull.com>.
    :license: BSD, see LICENSE for details
"""

__version__ = '0.01-dev'

from .session import Session
from .server import Server
from .window import Window
from .pane import Pane

from .util import live_tmux

from tmux import Server

from sh import tmux, cut, ErrorReturnCode_1


t = Server()
