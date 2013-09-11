# -*- coding: utf8 - *-
"""
    tmuxp.builder
    ~~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""

class Builder(object):
    '''
    used to build a configuration into a tmux real tmux workspace. creates and
    names windows, splits windows into panes.

    The normal phase of loading is:
        1. load the raw tmuxp config file
        2. kaplan imports files from json/yaml/ini to a python :class:`dict`
        3. :class:`ConfigExpand` expand's the dict's inline statements to full
           form
        4. :class:`ConfigTrickleDown` passes down default values from session
           -> window -> pane if applicable.
        5. (You are here) Builder loads the dict config. It will now create a
           :class:`Session` (a real ``tmux(1)`` session) and iterate through
           the list of windows, and their panes, returning full :class:`Window`
           and :class:`Pane` objects each step of the way.
    '''

    def __init__(self, config):
        '''

        :param: config: dict of configuration values
        '''
        self.config = config

    def build_session(self):
        '''
        returns :class:`Session` object.
        '''
        pass

    def build_window(self):
        '''
        returns :class:`Window` object.
        '''
        pass

    def build_pane(self):
        '''
        returns :class:`Pane` object.
        '''

