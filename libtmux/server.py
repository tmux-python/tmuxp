# -*- coding: utf-8 -*-
"""Pythonization of the :term:`tmux(1)` server.

libtmux.server
~~~~~~~~~~~~~~

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import os

from . import exc, formats
from .common import EnvironmentMixin, TmuxRelationalObject, tmux_cmd
from .session import Session

logger = logging.getLogger(__name__)


class Server(TmuxRelationalObject, EnvironmentMixin):

    """The :term:`tmux(1)` server.

    - :attr:`Server._sessions` [:class:`Session`, ...]

      - :attr:`Session._windows` [:class:`Window`, ...]

        - :attr:`Window._panes` [:class:`Pane`, ...]

          - :class:`Pane`

    When instantiated, provides the ``t`` global. stores information on live,
    running tmux server.

    """

    #: ``[-L socket-name]``
    socket_name = None
    #: ``[-S socket-path]``
    socket_path = None
    #: ``[-f file]``
    config_file = None
    #: ``-2`` or ``-8``
    colors = None
    #: unique child ID key
    childIdAttribute = 'session_id'

    def __init__(
        self,
        socket_name=None,
        socket_path=None,
        config_file=None,
        colors=None,
        **kwargs
    ):
        EnvironmentMixin.__init__(self, '-g')
        self._windows = []
        self._panes = []

        if socket_name:
            self.socket_name = socket_name

        if socket_path:
            self.socket_path = socket_path

        if config_file:
            self.config_file = config_file

        if colors:
            self.colors = colors

    def cmd(self, *args, **kwargs):
        """Return :class:`util.tmux_cmd` send tmux commands with sockets, colors.

        :rtype: :class:`util.tmux_cmd`

        :versionchanged: 0.8
            Renamed from ``.tmux`` to ``.cmd``.

        """

        args = list(args)
        if self.socket_name:
            args.insert(0, '-L{0}'.format(self.socket_name))
        if self.socket_path:
            args.insert(0, '-S{0}'.format(self.socket_path))
        if self.config_file:
            args.insert(0, '-f{0}'.format(self.config_file))
        if self.colors:
            if self.colors == 256:
                args.insert(0, '-2')
            elif self.colors == 88:
                args.insert(0, '-8')
            else:
                raise ValueError('Server.colors must equal 88 or 256')

        return tmux_cmd(*args, **kwargs)

    def _list_sessions(self):
        """Return list of sessions in :py:obj:`dict` form.

        Retrieved from ``$ tmux(1) list-sessions`` stdout.

        The :py:obj:`list` is derived from ``stdout`` in :class:`util.tmux_cmd`
        which wraps :py:class:`subprocess.Popen`.

        :rtype: :py:obj:`list` of :py:obj:`dict`

        """

        sformats = formats.SESSION_FORMATS
        tmux_formats = ['#{%s}' % f for f in sformats]

        tmux_args = (
            '-F%s' % '\t'.join(tmux_formats),   # output
        )

        proc = self.cmd(
            'list-sessions',
            *tmux_args
        )

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

        sformats = formats.SESSION_FORMATS
        tmux_formats = ['#{%s}' % format for format in sformats]
        sessions = proc.stdout

        # combine format keys with values returned from ``tmux list-windows``
        sessions = [dict(zip(
            sformats, session.split('\t'))) for session in sessions]

        # clear up empty dict
        sessions = [
            dict((k, v) for k, v in session.items() if v)
            for session in sessions
        ]

        return sessions

    @property
    def _sessions(self):
        """Property / alias to return :meth:`~._list_sessions`."""

        return self._list_sessions()

    def list_sessions(self):
        """Return list of :class:`Session` from the ``tmux(1)`` session.

        :rtype: :py:obj:`list` of :class:`Session`

        """
        return [
            Session(server=self, **s) for s in self._sessions
        ]

    @property
    def sessions(self):
        """Property / alias to return :meth:`~.list_sessions`."""
        return self.list_sessions()
    #: Alias of :attr:`sessions`.
    children = sessions

    def _list_windows(self):
        """Return list of windows in :py:obj:`dict` form.

        Retrieved from ``$ tmux(1) list-windows`` stdout.

        The :py:obj:`list` is derived from ``stdout`` in :class:`util.tmux_cmd`
        which wraps :py:class:`subprocess.Popen`.

        :rtype: list

        """

        wformats = ['session_name', 'session_id'] + formats.WINDOW_FORMATS
        tmux_formats = ['#{%s}' % format for format in wformats]

        proc = self.cmd(
            'list-windows',                     # ``tmux list-windows``
            '-a',
            '-F%s' % '\t'.join(tmux_formats),   # output
        )

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

        windows = proc.stdout

        wformats = ['session_name', 'session_id'] + formats.WINDOW_FORMATS

        # combine format keys with values returned from ``tmux list-windows``
        windows = [dict(zip(
            wformats, window.split('\t'))) for window in windows]

        # clear up empty dict
        windows = [
            dict((k, v) for k, v in window.items() if v) for window in windows
        ]

        # tmux < 1.8 doesn't have window_id, use window_name
        for w in windows:
            if 'window_id' not in w:
                w['window_id'] = w['window_name']

        if self._windows:
            self._windows[:] = []

        self._windows.extend(windows)

        return self._windows

    def _update_windows(self):
        """Update internal window data and return ``self`` for chainability.

        :rtype: :class:`Server`

        """
        self._list_windows()
        return self

    def _list_panes(self):
        """Return list of panes in :py:obj:`dict` form.

        Retrieved from ``$ tmux(1) list-panes`` stdout.

        The :py:obj:`list` is derived from ``stdout`` in :class:`util.tmux_cmd`
        which wraps :py:class:`subprocess.Popen`.

        :rtype: list

        """

        pformats = [
            'session_name', 'session_id',
            'window_index', 'window_id',
            'window_name'
        ] + formats.PANE_FORMATS
        tmux_formats = ['#{%s}\t' % f for f in pformats]

        proc = self.cmd(
            'list-panes',
            '-a',
            '-F%s' % ''.join(tmux_formats),     # output
        )

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

        panes = proc.stdout

        pformats = [
            'session_name', 'session_id',
            'window_index', 'window_id', 'window_name'
        ] + formats.PANE_FORMATS

        # combine format keys with values returned from ``tmux list-panes``
        panes = [dict(zip(
            pformats, window.split('\t'))) for window in panes]

        # clear up empty dict
        panes = [
            dict((k, v) for k, v in window.items() if v) for window in panes
        ]

        if self._panes:
            self._panes[:] = []

        self._panes.extend(panes)

        return self._panes

    def _update_panes(self):
        """Update internal pane data and return ``self`` for chainability.

        :rtype: :class:`Server`

        """
        self._list_panes()
        return self

    def attached_sessions(self):
        """Return active :class:`Session` objects.

        This will not work where multiple tmux sessions are attached.

        :rtype: :py:obj:`list` of :class:`Session`

        """

        sessions = self._sessions
        attached_sessions = list()

        for session in sessions:
            if 'session_attached' in session:
                # for now session_active is a unicode
                if session.get('session_attached') == '1':
                    logger.debug('session %s attached', session.get(
                        'session_name'))
                    attached_sessions.append(session)
                else:
                    continue

        return [
            Session(server=self, **s) for s in attached_sessions
        ] or None

    def has_session(self, target_session):
        """Return True if session exists. ``$ tmux has-session``.

        :param: target_session: str of session name.
        :rtype: bool

        """

        proc = self.cmd('has-session', '-t%s' % target_session)

        if not proc.stdout:
            return True
        if any(
            x in proc.stdout for x in
            ['failed to connect to server', 'error connecting to']
        ):
            return False
        elif 'no server running' in proc.stdout:  # tmux 2.0
            return False
        elif 'can\'t find session' in proc.stdout:  # tmux 2.1
            return False
        elif 'session not found' in proc.stdout:
            return False
        else:
            return True

    def kill_server(self):
        """``$ tmux kill-server``."""
        self.cmd('kill-server')

    def kill_session(self, target_session=None):
        """Kill the tmux session with ``$ tmux kill-session``, return ``self``.

        :param: target_session: str. note this accepts ``fnmatch(3)``. 'asdf'
            will kill 'asdfasd'.

        :rtype: :class:`Server`

        """
        proc = self.cmd('kill-session', '-t%s' % target_session)

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

        return self

    def switch_client(self, target_session):
        """``$ tmux switch-client``.

        :param: target_session: str. name of the session. fnmatch(3) works.

        """

        proc = self.cmd('switch-client', '-t%s' % target_session)

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

    def attach_session(self, target_session=None):
        """``$ tmux attach-session`` aka alias: ``$ tmux attach``.

        :param: target_session: str. name of the session. fnmatch(3) works.

        """
        tmux_args = tuple()
        if target_session:
            tmux_args += ('-t%s' % target_session,)

        proc = self.cmd('attach-session', *tmux_args)

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

    def new_session(self,
                    session_name=None,
                    kill_session=False,
                    attach=False,
                    *args,
                    **kwargs):
        """Return :class:`Session` from  ``$ tmux new-session``.

        Uses ``-P`` flag to print session info, ``-F`` for return formatting
        returns new Session object.

        ``$ tmux new-session -d`` will create the session in the background
        ``$ tmux new-session -Ad`` will move to the session name if it already
        exists. todo: make an option to handle this.

        :param session_name: session name::

            $ tmux new-session -s <session_name>
        :type session_name: string

        :param attach: create session in the foreground. ``attach=False`` is
        equivalent to::

            $ tmux new-session -d
        :type attach: bool

        :param kill_session: Kill current session if ``$ tmux has-session``
                             Useful for testing workspaces.
        :type kill_session: bool
        :rtype: :class:`Session`

        """

        if self.has_session(session_name):
            if kill_session:
                self.cmd('kill-session', '-t%s' % session_name)
                logger.info('session %s exists. killed it.' % session_name)
            else:
                raise exc.TmuxSessionExists(
                    'Session named %s exists' % session_name
                )

        logger.debug('creating session %s' % session_name)

        sformats = formats.SESSION_FORMATS
        tmux_formats = ['#{%s}' % f for f in sformats]

        env = os.environ.get('TMUX')

        if env:
            del os.environ['TMUX']

        tmux_args = (
            '-s%s' % session_name,
            '-P', '-F%s' % '\t'.join(tmux_formats),   # output
        )

        if not attach:
            tmux_args += ('-d',)

        proc = self.cmd(
            'new-session',
            *tmux_args
        )

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

        session = proc.stdout[0]

        if env:
            os.environ['TMUX'] = env

        # combine format keys with values returned from ``tmux list-windows``
        session = dict(zip(sformats, session.split('\t')))

        # clear up empty dict
        session = dict((k, v) for k, v in session.items() if v)

        session = Session(server=self, **session)

        return session
