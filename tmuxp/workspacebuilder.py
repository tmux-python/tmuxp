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
    Build tmux workspace from a configuration. Creates and names windows, sets
    options, splits windows into panes.

    The normal phase of loading is:

        1.  :ref:`kaptan` imports json/yaml/ini. ``.get()`` returns
            python :class:`dict`.

            .. code-block:: python
                import kaptan
                sconf = kaptan.Kaptan(handler='yaml')
                sconf = sconfig.import_config(self.yaml_config).get()

            or from config file with extension:

            .. code-block:: python

                import kaptan
                sconf = kaptan.Kaptan()
                sconf = sconfig.import_config('path/to/config.yaml').get()

            kaptan automatically detects the handler from filenames.
        2.  :meth:`config.expand` sconf inline shorthand

            .. code-block:: python

                from tmuxp import config
                sconf = config.expand(sconf)

        3.  :meth:`config.trickle` passes down default values from session
            -> window -> pane if applicable.

            .. code-block:: python

                sconf = config.trickle(sconf)

        4.  (You are here) We will create a :class:`Session` (a real
            ``tmux(1)`` session) and iterate through the list of windows, and
            their panes, returning full :class:`Window` and :class:`Pane`
            objects each step of the way.

            .. code-block:: python

                workspace = WorkspaceBuilder(sconf=sconf)

    It handles the magic of cases where the user may want to start
    a session inside tmux (when `$TMUX` is in the env variables).

    '''

    def __init__(self, sconf):
        '''
        todo: initialize :class:`Session` from here, in ``self.session``.

        :param sconf: session config, includes a :py:obj:`list` of ``windows``.
        :type sconf: :py:obj:`dict`
        '''

        if not 'session_name' in sconf:
            raise ValueError('config requires session_name')

        self.sconf = sconf

    def iter_create_windows(self, s):
        ''' generator that creates tmux windows, yields :class:`Window` object
        by iterating through ``sconf['windows']``.

        todo: look at this tomorrow: may not be necessary to have session.

        :param session: :class:`Session` from the config
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
