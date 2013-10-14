# -*- coding: utf8 - *-
"""
    tmuxp.cli
    ~~~~~~~~~

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""

import os
import logging
from . import log

logger = logging.getLogger(__name__)


def setupLogger(logger=None):
    '''setup logging for CLI use.

    :param logger: instance of logger
    :type logger: :py:class:`Logger`
    '''
    if not logger:
        logger = logging.getLogger()
    if not logger.handlers:
        channel = logging.StreamHandler()
        channel.setFormatter(log.LogFormatter())
        logger.setLevel('INFO')
        logger.addHandler(channel)


def startup(config_dir):
    ''' set up cli interface '''

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    configs = []
    configs = [(dirpath, dirname, filenames) for (dirpath, dirname, filenames) in os.walk(config_dir)]
    for config in configs:
        logger.info(config)


def main():
    setupLogger()

    logger.info('output')
    logger.info(__name__)

    # does config dir exist
    config_dir = os.path.expanduser('~/.tmuxp')

    startup(config_dir)
