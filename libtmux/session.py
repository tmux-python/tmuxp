# -*- coding: utf-8 -*-
"""Pythonization of the :term:`tmux(1)` session.

libtmux.session
~~~~~~~~~~~~~~~

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import os

from . import exc, formats
from .common import EnvironmentMixin, TmuxMappingObject, TmuxRelationalObject
from .window import Window

logger = logging.getLogger(__name__)


class Session(
    TmuxMappingObject,
    TmuxRelationalObject,
    EnvironmentMixin
):
    """:term:`tmux(1)` session.

    Holds :class:`Window` objects.

    """

    childIdAttribute = 'window_id'

    def __init__(self, server=None, **kwargs):
        EnvironmentMixin.__init__(self)
        self.server = server

        if 'session_id' not in kwargs:
            raise ValueError('Session requires a `session_id`')
        self._session_id = kwargs['session_id']
        self.server._update_windows()

    @property
    def _TMUX(self, *args):

        attrs = {
            'session_id': str(self._session_id)
        }

        # from https://github.com/serkanyersen/underscore.py
        def by(val, *args):
            for key, value in attrs.items():
                try:
                    if attrs[key] != val[key]:
                        return False
                except KeyError:
                    return False
                return True

        try:
            return list(filter(by, self.server._sessions))[0]
        except IndexError as e:
            logger.error(e)

    def cmd(self, *args, **kwargs):
        """Return :meth:`server.cmd`.

        :rtype: :class:`server.cmd`

        :versionchanged: 0.8
            Renamed from ``.tmux`` to ``.cmd``.

        """
        if '-t' not in kwargs:
            kwargs['-t'] = self.get('session_id')
        return self.server.cmd(*args, **kwargs)

    def attach_session(self, target_session=None):
        """Return ``$ tmux attach-session`` aka alias: ``$ tmux attach``.

        :param: target_session: str. name of the session. fnmatch(3) works.

        """
        proc = self.cmd('attach-session', '-t%s' % self.get('session_id'))

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

    def kill_session(self):
        """``$ tmux kill-session``."""

        proc = self.cmd('kill-session', '-t%s' % self.get('session_id'))

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

    def switch_client(self, target_session=None):
        """``$ tmux switch-client``.

        :param: target_session: str. note this accepts fnmatch(3).
        """
        proc = self.cmd('switch-client', '-t%s' % self.get('session_id'))

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

    def rename_session(self, new_name):
        """Rename session and return new :class:`Session` object.

        :param rename_session: new session name
        :type rename_session: string
        :rtype: :class:`Session`

        """
        proc = self.cmd(
            'rename-session',
            '-t%s' % self.get('session_id'),
            new_name
        )

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

        return self

    def new_window(self,
                   window_name=None,
                   start_directory=None,
                   attach=True,
                   window_index='',
                   window_shell=None):
        """Return :class:`Window` from ``$ tmux new-window``.

        .. note::

            By default, this will make the window active. For the new window
            to be created and not set to current, pass in ``attach=False``.

        :param window_name: window name.

        .. code-block:: bash

            $ tmux new-window -n <window_name> -c <start_directory>

        :type window_name: string
        :param start_directory: specifies the working directory in which the
            new created.
        :type start_directory: string
        :param attach: make new window the current window after creating it,
                       default True.
        :param window_index: create the new window at the given index position.
            Default is empty string which will create the window in the next
            available position.
        :type window_index: string
        :param window_shell: execute a command on starting the window.  The
            window will close when the command exits.
            NOTE: When this command exits the window will close.  This feature
            is useful for long-running processes where the closing of the
            window upon completion is desired.
        :type window_command: string
        :param type: bool
        :rtype: :class:`Window`

        """

        wformats = ['session_name', 'session_id'] + formats.WINDOW_FORMATS
        tmux_formats = ['#{%s}' % f for f in wformats]

        window_args = tuple()

        if not attach:
            window_args += ('-d',)

        window_args += (
            '-P',
        )

        if start_directory:
            # as of 2014-02-08 tmux 1.9-dev doesn't expand ~ in new-window -c.
            start_directory = os.path.expanduser(start_directory)
            window_args += ('-c%s' % start_directory,)

        window_args += (
            '-F"%s"' % '\t'.join(tmux_formats),  # output
        )
        if window_name:
            window_args += ('-n%s' % window_name,)

        window_args += (
            # empty string for window_index will use the first one available
            '-t%s:%s' % (self.get('session_id'), window_index),
        )

        if window_shell:
            window_args += (window_shell,)

        proc = self.cmd('new-window', *window_args)

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

        window = proc.stdout[0]

        window = dict(zip(wformats, window.split('\t')))

        # clear up empty dict
        window = dict((k, v) for k, v in window.items() if v)
        window = Window(session=self, **window)

        self.server._update_windows()

        return window

    def kill_window(self, target_window=None):
        """``$ tmux kill-window``.

        Kill the current window or the window at ``target-window``. removing it
        from any sessions to which it is linked.

        :param target_window: the ``target window``.
        :type target_window: string

        """

        if target_window:
            if isinstance(target_window, int):
                target = '-t%s:%d' % (self.get('session_name'), target_window)
            else:
                target = '-t%s' % target_window

        proc = self.cmd('kill-window', target)

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

        self.server._update_windows()

    def _list_windows(self):
        windows = self.server._update_windows()._windows

        windows = [
            w for w in windows if w['session_id'] == self.get('session_id')
        ]

        return windows

    @property
    def _windows(self):
        """Property / alias to return :meth:`~._list_windows`."""

        return self._list_windows()

    def list_windows(self):
        """Return a list of :class:`Window` from the ``tmux(1)`` session.

        :rtype: :class:`Window`

        """
        windows = [
            w for w in self._windows if w['session_id'] == self._session_id
        ]

        return [Window(session=self, **window) for window in windows]

    @property
    def windows(self):
        """Property / alias to return :meth:`~.list_windows`."""
        return self.list_windows()

    #: Alias of :attr:`windows`.
    children = windows

    def attached_window(self):
        """Return active :class:`Window` object.

        :rtype: :class:`Window`

        """
        active_windows = []
        for window in self._windows:
            if 'window_active' in window:
                # for now window_active is a unicode
                if window.get('window_active') == '1':
                    active_windows.append(Window(session=self, **window))
                else:
                    continue

        if len(active_windows) == int(1):
            return active_windows[0]
        else:
            raise exc.LibTmuxException(
                'multiple active windows found. %s' % active_windows)

        if len(self._windows) == int(0):
            raise exc.LibTmuxException('No Windows')

    def select_window(self, target_window):
        """Return :class:`Window` selected via ``$ tmux select-window``.

        :param: window: ``target_window`` also 'last-window' (``-l``),
                        'next-window' (``-n``), or 'previous-window' (``-p``)
        :type window: integer
        :rtype: :class:`Window`

        :todo: assure ``-l``, ``-n``, ``-p`` work.

        """

        target = '-t%s' % target_window

        proc = self.cmd('select-window', target)

        if proc.stderr:
            raise exc.LibTmuxException(proc.stderr)

        return self.attached_window()

    def attached_pane(self):
        """Return active :class:`Pane` object."""

        return self.attached_window().attached_pane()

    def set_option(self, option, value):
        """Set option ``$ tmux set-option <option> <value>``.

        todo: needs tests

        :param option: the window option. such as 'default-shell'.
        :type option: string
        :param value: window value. True/False will turn in 'on' and 'off'. You
            can also enter 'on' or 'off' directly.
        :type value: bool

        """

        if isinstance(value, bool) and value:
            value = 'on'
        elif isinstance(value, bool) and not value:
            value = 'off'

        proc = self.cmd(
            'set-option', option, value
        )

        if proc.stderr:
            if isinstance(proc.stderr, list) and len(proc.stderr) == int(1):
                proc.stderr = proc.stderr[0]
            raise ValueError('tmux set-option stderr: %s' % proc.stderr)

    def show_options(self, option=None, g=False):
        """Return a dict of options for the window.

        For familiarity with tmux, the option ``option`` param forwards to pick
        a single option, forwarding to :meth:`Session.show_option`.

        :param option: optional. show a single option.
        :type option: string
        :param g: Pass ``-g`` flag for global variable
        :type g: bool
        :rtype: :py:obj:`dict`

        """

        tmux_args = tuple()

        if g:
            tmux_args += ('-g',)

        if option:
            return self.show_option(option, g=g)
        else:
            tmux_args += ('show-options',)
            session_options = self.cmd(
                *tmux_args
            ).stdout

        session_options = [tuple(item.split(' ')) for item in session_options]

        session_options = dict(session_options)

        for key, value in session_options.items():
            if value.isdigit():
                session_options[key] = int(value)

        return session_options

    def show_option(self, option, g=False):
        """Return a list of options for the window.

        :todo: test and return True/False for on/off string

        :param option: option to return.
        :type option: string
        :rtype: string, int or bool

        """

        tmux_args = tuple()

        if g:
            tmux_args += ('-g',)

        window_option = self.cmd(
            'show-options', option, *tmux_args
        ).stdout
        window_option = [tuple(item.split(' ')) for item in window_option][0]

        if window_option[1].isdigit():
            window_option = (window_option[0], int(window_option[1]))

        return window_option[1]

    def __repr__(self):
        return "%s(%s %s)" % (
            self.__class__.__name__,
            self.get('session_id'),
            self.get('session_name')
        )
