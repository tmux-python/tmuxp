# -*- coding: utf8 - *-
"""
    tmuxp.exc
    ~~~~~~~~~
    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""

class TmuxSessionNotFound(Exception):
    pass

class TmuxSessionExists(Exception):
    pass

class TmuxNoClientsRunning(Exception):
    pass

class TmuxNotRunning(Exception):
    '''
    tmux server not running.
    '''
    pass

class EmptyConfigException(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)
