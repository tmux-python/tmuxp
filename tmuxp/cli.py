# -*- coding: utf8 - *-
"""
    tmuxp.cli
    ~~~~~~~~~

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""

import logging
from . import log

logger = logging.getLogger(__name__)


def setupLogger(logger=None):

    if not logger:
        logger = logging.getLogger()
    if not logger.handlers:
        channel = logging.StreamHandler()
        channel.setFormatter(log.LogFormatter())
        logger.setLevel('INFO')
        logger.addHandler(channel)


def main():
    setupLogger()

    logger.info('output')
    logger.info(__name__)
