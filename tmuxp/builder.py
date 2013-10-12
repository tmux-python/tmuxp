# -*- coding: utf8 - *-
"""
    tmuxp.builder
    ~~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""

from __future__ import absolute_import, division, print_function, with_statement
from . import log
import logging

logger = logging.getLogger(__name__)


class Builder(object):
    '''
    used to build a configuration into a tmux real tmux workspace. creates and
    names windows, splits windows into panes.

    The normal phase of loading is:
        1. load the raw tmuxp config file
        2. kaplan imports files from json/yaml/ini to a python :class:`dict`
        3. :meth:`config.expand` expand's the dict's inline statements to full
           form
        4. :meth:`config.trickle` passes down default values from session
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

    def iter_create_windows(self, s, sconf):
        ''' this is a generator that will create the windows and return the
        :class:`Window` object for the window.

        It handles the magic of cases where the user may want to start
        a session inside tmux (when `$TMUX` is in the env variables).

        :param: session: :class:`Session` from the config
        :param: sconf: :py:obj:`dict` session config, includes a :py:obj:`list`
            of ``windows``.
        '''

        for i, wconf in enumerate(sconf['windows'], start=1):
            automatic_rename = False
            if 'window_name' not in wconf:
                window_name = None
                automatic_rename = True
            else:
                window_name = wconf['window_name']

            if i == int(1):  # if first window, use window 1
                #w = s.select_window(1)
                w = s.attached_window()
                w = w.rename_window(window_name)
            else:
                w = s.new_window(
                    window_name=window_name,
                    automatic_rename=automatic_rename
                )

            w.list_panes()
            yield w, wconf

    def iter_create_panes(self, w, wconf):
        for pindex, pconf in enumerate(wconf['panes'], start=1):
            if pindex != int(1):
                p = w.split_window()
            else:
                p = w.attached_pane()
            for cmd in pconf['shell_command']:
                p.send_keys(cmd)

            w.list_panes()

            yield p
