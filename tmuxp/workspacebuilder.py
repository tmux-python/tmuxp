# -*- coding: utf-8 -*-
"""Create a tmux workspace from a configuration :py:obj:`dict`.

tmuxp.workspacebuilder
~~~~~~~~~~~~~~~~~~~~~~

"""

from __future__ import absolute_import, unicode_literals

import logging

from libtmux.exc import TmuxSessionExists
from libtmux.pane import Pane
from libtmux.server import Server
from libtmux.session import Session
from libtmux.window import Window

from . import exc
from .util import run_before_script, get_current_pane

logger = logging.getLogger(__name__)


class WorkspaceBuilder(object):

    """
    Load workspace from session :py:obj:`dict`.

    Build tmux workspace from a configuration. Creates and names windows, sets
    options, splits windows into panes.

    The normal phase of loading is:

    1. :term:`kaptan` imports json/yaml/ini. ``.get()`` returns python
       :class:`dict`::

           import kaptan
           sconf = kaptan.Kaptan(handler='yaml')
           sconf = sconfig.import_config(self.yaml_config).get()

       or from config file with extension::

           import kaptan
           sconf = kaptan.Kaptan()
           sconf = sconfig.import_config('path/to/config.yaml').get()

       kaptan automatically detects the handler from filenames.

    2. :meth:`config.expand` sconf inline shorthand::

           from tmuxp import config
           sconf = config.expand(sconf)

    3. :meth:`config.trickle` passes down default values from session
       -> window -> pane if applicable::

           sconf = config.trickle(sconf)

    4. (You are here) We will create a :class:`libtmux.Session` (a real
       ``tmux(1)`` session) and iterate through the list of windows, and
       their panes, returning full :class:`libtmux.Window` and
       :class:`libtmux.Pane` objects each step of the way::

           workspace = WorkspaceBuilder(sconf=sconf)

    It handles the magic of cases where the user may want to start
    a session inside tmux (when `$TMUX` is in the env variables).
    """

    def __init__(self, sconf, plugins=[], server=None):
        """
        Initialize workspace loading.

        Parameters
        ----------
        sconf : dict
            session config, includes a :py:obj:`list` of ``windows``.

        plugins : list
            plugins to be used for this session

        server : :class:`libtmux.Server`
            tmux server to build session in

        Notes
        -----
        TODO: Initialize :class:`libtmux.Session` from here, in
        ``self.session``.
        """

        if not sconf:
            raise exc.EmptyConfigException('session configuration is empty.')

        # config.validate_schema(sconf)

        if isinstance(server, Server):
            self.server = server
        else:
            self.server = None

        self.sconf = sconf

        self.plugins = plugins

    def session_exists(self, session_name=None):
        exists = self.server.has_session(session_name)
        if not exists:
            return exists

        self.session = self.server.find_where({'session_name': session_name})
        return True

    def build(self, session=None, append=False):
        """
        Build tmux workspace in session.

        Optionally accepts ``session`` to build with only session object.

        Without ``session``, it will use :class:`libmtux.Server` at
        ``self.server`` passed in on initialization to create a new Session
        object.

        Parameters
        ----------
        session : :class:`libtmux.Session`
            session to build workspace in
        append : bool
            append windows in current active session
        """

        if not session:
            if not self.server:
                raise exc.TmuxpException(
                    'WorkspaceBuilder.build requires server to be passed '
                    + 'on initialization, or pass in session object to here.'
                )

            if self.server.has_session(self.sconf['session_name']):
                self.session = self.server.find_where(
                    {'session_name': self.sconf['session_name']}
                )
                raise TmuxSessionExists(
                    'Session name %s is already running.' % self.sconf['session_name']
                )
            else:
                if 'start_directory' in self.sconf:
                    session = self.server.new_session(
                        session_name=self.sconf['session_name'],
                        start_directory=self.sconf['start_directory'],
                    )
                else:
                    session = self.server.new_session(
                        session_name=self.sconf['session_name']
                    )

            assert self.sconf['session_name'] == session.name
            assert len(self.sconf['session_name']) > 0

        self.session = session
        self.server = session.server

        self.server._list_sessions()
        assert self.server.has_session(session.name)
        assert session.id

        assert isinstance(session, Session)

        for plugin in self.plugins:
            plugin.before_workspace_builder(self.session)

        focus = None

        if 'before_script' in self.sconf:
            try:
                cwd = None

                # we want to run the before_script file cwd'd from the
                # session start directory, if it exists.
                if 'start_directory' in self.sconf:
                    cwd = self.sconf['start_directory']
                run_before_script(self.sconf['before_script'], cwd=cwd)
            except Exception as e:
                self.session.kill_session()
                raise e
        if 'options' in self.sconf:
            for option, value in self.sconf['options'].items():
                self.session.set_option(option, value)
        if 'global_options' in self.sconf:
            for option, value in self.sconf['global_options'].items():
                self.session.set_option(option, value, _global=True)
        if 'environment' in self.sconf:
            for option, value in self.sconf['environment'].items():
                self.session.set_environment(option, value)

        for w, wconf in self.iter_create_windows(session, append):
            assert isinstance(w, Window)

            for plugin in self.plugins:
                plugin.on_window_create(w)

            focus_pane = None
            for p, pconf in self.iter_create_panes(w, wconf):
                assert isinstance(p, Pane)
                p = p

                if 'layout' in wconf:
                    w.select_layout(wconf['layout'])

                if 'focus' in pconf and pconf['focus']:
                    focus_pane = p

            if 'focus' in wconf and wconf['focus']:
                focus = w

            self.config_after_window(w, wconf)

            for plugin in self.plugins:
                plugin.after_window_finished(w)

            if focus_pane:
                focus_pane.select_pane()

        if focus:
            focus.select_window()

    def iter_create_windows(self, session, append=False):
        """
        Return :class:`libtmux.Window` iterating through session config dict.

        Generator yielding :class:`libtmux.Window` by iterating through
        ``sconf['windows']``.

        Applies ``window_options`` to window.

        Parameters
        ----------
        session : :class:`libtmux.Session`
            session to create windows in
        append : bool
            append windows in current active session

        Returns
        -------
        tuple of (:class:`libtmux.Window`, ``wconf``)
            Newly created window, and the section from the tmuxp configuration
            that was used to create the window.
        """
        for i, wconf in enumerate(self.sconf['windows'], start=1):
            if 'window_name' not in wconf:
                window_name = None
            else:
                window_name = wconf['window_name']

            is_first_window_pass = self.first_window_pass(i, session, append)

            w1 = None
            if is_first_window_pass:  # if first window, use window 1
                w1 = session.attached_window
                w1.move_window(99)

            if 'start_directory' in wconf:
                sd = wconf['start_directory']
            else:
                sd = None

            if 'window_shell' in wconf:
                ws = wconf['window_shell']
            else:
                ws = None

            w = session.new_window(
                window_name=window_name,
                start_directory=sd,
                attach=False,  # do not move to the new window
                window_index=wconf.get('window_index', ''),
                window_shell=ws,
            )

            if is_first_window_pass:  # if first window, use window 1
                session.attached_window.kill_window()

            assert isinstance(w, Window)
            session.server._update_windows()
            if 'options' in wconf and isinstance(wconf['options'], dict):
                for key, val in wconf['options'].items():
                    w.set_window_option(key, val)

            if 'focus' in wconf and wconf['focus']:
                w.select_window()

            session.server._update_windows()

            yield w, wconf

    def iter_create_panes(self, w, wconf):
        """
        Return :class:`libtmux.Pane` iterating through window config dict.

        Run ``shell_command`` with ``$ tmux send-keys``.

        Parameters
        ----------
        w : :class:`libtmux.Window`
            window to create panes for
        wconf : dict
            config section for window

        Returns
        -------
        tuple of (:class:`libtmux.Pane`, ``pconf``)
            Newly created pane, and the section from the tmuxp configuration
            that was used to create the pane.
        """
        assert isinstance(w, Window)

        pane_base_index = int(w.show_window_option('pane-base-index', g=True))

        p = None

        for pindex, pconf in enumerate(wconf['panes'], start=pane_base_index):
            if pindex == int(pane_base_index):
                p = w.attached_pane
            else:

                def get_pane_start_directory():

                    if 'start_directory' in pconf:
                        return pconf['start_directory']
                    elif 'start_directory' in wconf:
                        return wconf['start_directory']
                    else:
                        return None

                p = w.split_window(
                    attach=True, start_directory=get_pane_start_directory(), target=p.id
                )

            assert isinstance(p, Pane)
            if 'layout' in wconf:
                w.select_layout(wconf['layout'])

            if 'suppress_history' in pconf:
                suppress = pconf['suppress_history']
            elif 'suppress_history' in wconf:
                suppress = wconf['suppress_history']
            else:
                suppress = True

            for cmd in pconf['shell_command']:
                p.send_keys(cmd, suppress_history=suppress)

            if 'focus' in pconf and pconf['focus']:
                w.select_pane(p['pane_id'])

            w.server._update_panes()

            yield p, pconf

    def config_after_window(self, w, wconf):
        """Actions to apply to window after window and pane finished.

        When building a tmux session, sometimes its easier to postpone things
        like setting options until after things are already structurally
        prepared.

        Parameters
        ----------
        w : :class:`libtmux.Window`
            window to create panes for
        wconf : dict
            config section for window
        """
        if 'options_after' in wconf and isinstance(wconf['options_after'], dict):
            for key, val in wconf['options_after'].items():
                w.set_window_option(key, val)

    def find_current_attached_session(self):
        current_active_pane = get_current_pane(self.server)

        if not current_active_pane:
            raise exc.TmuxpException("No session active.")

        return next(
            (
                s
                for s in self.server.list_sessions()
                if s["session_id"] == current_active_pane["session_id"]
            ),
            None,
        )

    def first_window_pass(self, i, session, append):
        return len(session.windows) == 1 and i == 1 and not append


def freeze(session):
    """
    Freeze live tmux session and Return session config :py:obj:`dict`.

    Parameters
    ----------
    session : :class:`libtmux.Session`
        session object

    Returns
    -------
    dict
        tmuxp compatible workspace config
    """
    sconf = {'session_name': session['session_name'], 'windows': []}

    for w in session.windows:
        wconf = {
            'options': w.show_window_options(),
            'window_name': w.name,
            'layout': w.layout,
            'panes': [],
        }
        if w.get('window_active', '0') == '1':
            wconf['focus'] = 'true'

        # If all panes have same path, set 'start_directory' instead
        # of using 'cd' shell commands.
        def pane_has_same_path(p):
            return w.panes[0].current_path == p.current_path

        if all(pane_has_same_path(p) for p in w.panes):
            wconf['start_directory'] = w.panes[0].current_path

        for p in w.panes:
            pconf = {'shell_command': []}

            if 'start_directory' not in wconf:
                pconf['shell_command'].append('cd ' + p.current_path)

            if p.get('pane_active', '0') == '1':
                pconf['focus'] = 'true'

            current_cmd = p.current_command

            def filter_interpretters_and_shells():
                return current_cmd.startswith('-') or any(
                    current_cmd.endswith(cmd) for cmd in ['python', 'ruby', 'node']
                )

            if filter_interpretters_and_shells():
                current_cmd = None

            if current_cmd:
                pconf['shell_command'].append(current_cmd)
            else:
                if not len(pconf['shell_command']):
                    pconf = 'pane'

            wconf['panes'].append(pconf)

        sconf['windows'].append(wconf)

    return sconf
