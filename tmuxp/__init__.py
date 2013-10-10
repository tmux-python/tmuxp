# -*- coding: utf8 - *-
"""
    tmuxp
    ~~~~~

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""


from __future__ import absolute_import, division, print_function, with_statement

from .session import Session
from .server import Server
from .window import Window
from .pane import Pane
from .builder import Builder
from .config import expand_config, trickledown_config

from .util import TmuxObject

__version__ = '0.0.1-dev'


def main():
    from . import log
    import logging

    logger = logging.getLogger()
    channel = logging.StreamHandler()
    channel.setFormatter(log.LogFormatter())
    logger.setLevel('INFO')
    logger.addHandler(channel)
    logger.info('output')
    pass
