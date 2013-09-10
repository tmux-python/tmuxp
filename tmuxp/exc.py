# -*- coding: utf8 - *-
"""
    tmuxp.exc
    ~~~~~~~~~
    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from sh import ErrorReturnCode_1


class TmuxSessionNotFound(Exception):
    pass


class TmuxSessionExists(Exception):
    pass


class TmuxNotRunning(Exception):
    '''
        class for when {pane,window,session}_id doesn't exist, this will cause
        an issue with building the workspace and running commands.
    '''
    pass
