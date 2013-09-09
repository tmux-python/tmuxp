# -*- coding: utf8 - *-
"""
    tmuxp.exc
    ~~~~~~~~~
    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""


class SessionNotFound(Exception):
    pass


class SessionExists(Exception):
    pass


class TmuxNotRunning(Exception):
    '''
        class for when {pane,window,session}_id doesn't exist, this will cause
        an issue with building the workspace and running commands.
    '''
    pass
