# -*- coding: utf8 - *-
"""
    tmuxp.builder
    ~~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""

from __future__ import absolute_import, division, print_function, with_statement
import logging

logger = logging.getLogger(__name__)


class WorkspaceBuilder(object):
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

    ``sconf`` is the configuration from yaml/json/config after it has been:

    1.  imported through :ref:`kaptan`:

        .. code-block:: python

            sconf = kaptan.Kaptan(handler='yaml')
            sconf = sconfig.import_config(self.yaml_config).get()

        or from config file:

        .. code-block:: python

            sconf = kaptan.Kaptan()
            sconf = sconfig.import_config('path/to/config.yaml').get()

        kaptan automatically detects the handler from filenames.

    2.  had inline config shortcuts expanded with :meth:`config.expand`

        .. code-block:: python

            from tmuxp import config
            sconf = config.expand(sconf)

    3.  has passed down certain keys such as ``shell_command_before`` to
        child window and pane items with :meth:`config.trickle`:

        .. code-block:: python

            from tmuxp import config
            sconf = config.trickle(sconf)

    It handles the magic of cases where the user may want to start
    a session inside tmux (when `$TMUX` is in the env variables).

    '''

    def __init__(self, sconf):
        '''
        :param: sconf: :py:obj:`dict` session config, includes a :py:obj:`list`
            of ``windows``.
        '''

        if not 'session_name' in sconf:
            raise ValueError('config requires session_name')

        self.sconf = sconf

    def iter_create_windows(self, s):
        ''' generator that creates tmux windows, yields :class:`Window` object
        by iterating through ``sconf['windows']``.

        :param: session: :class:`Session` from the config
        '''
        for i, wconf in enumerate(self.sconf['windows'], start=1):
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

            if 'options' in wconf and isinstance(wconf['options'], dict):
                for key, val in wconf['options'].iteritems():
                    w.set_window_option(key, val)
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
