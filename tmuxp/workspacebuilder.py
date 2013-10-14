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
from . import exc

logger = logging.getLogger(__name__)


def check_consistency(sconf):
    '''Verify the consistency of the config file.

    Config files in tmuxp are met to import into :py:mod:`dict`.
    '''

    # verify session_name
    if not 'session_name' in sconf:
        raise exc.ConfigError('config requires session_name')

    if not 'windows' in sconf:
        raise exc.ConfigError('config requires windows')

    for window in sconf['windows']:
        if not 'window_name' in window:
            raise exc.ConfigError('config window is missing "window_name"')

        if not 'panes' in window:
            raise exc.ConfigError('config window %s requires panes' % window['window_name'])

    return True


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

    def __init__(self, sconf, server=None):
        '''
        todo: initialize :class:`Session` from here, in ``self.session``.

        :param sconf: session config, includes a :py:obj:`list` of ``windows``.
        :type sconf: :py:obj:`dict`

        :param server:
        :type server: :class:`Server`
        '''

        if not sconf:
            raise exc.EmptyConfigException('session configuration is empty.')

        check_consistency(sconf)

        if server:
            self.server = server

        self.sconf = sconf

    def build(self):
        '''high-level builder, relies on :attr:`server`.'''

        if self.server.has_session(self.sconf['session_name']):
            raise exc.TmuxSessionExists('Session name %s is already running.' %
                                        self.sconf['session_name'])
        else:
            session = self.server.new_session(session_name=self.sconf['session_name'])

        window_count = len(session._windows)  # current window count
        for w, wconf in self.iter_create_windows(session):

            window_pane_count = len(w._panes)
            for p in self.iter_create_panes(w, wconf):
                p = p

            w.set_window_option('main-pane-height', 50)
            w.select_layout(wconf['layout'])

    def iter_create_windows(self, s):
        ''' generator that creates tmux windows, yields :class:`Window` object
        by iterating through ``sconf['windows']``.

        todo: look at this tomorrow: may not be necessary to have session.

        will also apply ``window_options`` to window.

        :param session: :class:`Session` from the config
        :rtype: :class:`Window`
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
        ''' generator creating and yielding panes for Window + window config
        section.

        will also run ``shell_command`` with ``$ tmux send-keys``.

        :param w: window to create panes for
        :type w: :class:`Window`
        :param wconf: config section for window
        :type wconf: :py:obj:`dict`
        :rtype: :class:`Pane`
        '''

        for pindex, pconf in enumerate(wconf['panes'], start=1):
            if pindex != int(1):
                p = w.split_window()
            else:
                p = w.attached_pane()
            for cmd in pconf['shell_command']:
                p.send_keys(cmd)

            w.list_panes()

            yield p
