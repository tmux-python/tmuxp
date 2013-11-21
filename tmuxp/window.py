# -*- coding: utf8 - *-
"""Pythonization of the :term:`tmux(1)` window.

tmuxp.window
~~~~~~~~~~~~

tmuxp helps you manage tmux workspaces.

:copyright: Copyright 2013 Tony Narlock.
:license: BSD, see LICENSE for details

"""
from __future__ import absolute_import, division, print_function, with_statement

import pipes
from .pane import Pane

from . import util, formats, exc
import logging

logger = logging.getLogger(__name__)


class Window(util.TmuxMappingObject, util.TmuxRelationalObject):

    """:term:`tmux(1)` window."""

    childIdAttribute = 'pane_id'

    def __init__(self, session=None, **kwargs):

        if not session:
            raise ValueError('Window requires a Session, session=Session')

        self.session = session
        self.server = self.session.server

        if not 'window_id' in kwargs:
            raise ValueError('Window requires a `window_id`')

        self._window_id = kwargs['window_id']

    def __repr__(self):
        return "%s(%s %s:%s, %s)" % (
            self.__class__.__name__,
            self.get('window_id'),
            self.get('window_index'),
            self.get('window_name'),
            self.session
        )

    @property
    def _TMUX(self, *args):

        attrs = {
            'window_id': self._window_id
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

        return list(filter(by, self.server._windows))[0]

    def tmux(self, cmd, *args, **kwargs):
        """Return :meth:`Server.tmux` defaulting ``target_window`` as target.

        Send command to tmux with :attr:`window_id` as ``target-window``.

        Specifying ``('-t', 'custom-target')`` or ``('-tcustom_target')`` in
        ``args`` will override using the object's ``window_id`` as target.

        :rtype: :class:`Server.tmux`

        """
        if not len([arg for arg in args if '-t' in str(arg)]):
            args = ('-t', self.get('window_id')) + args

        return self.server.tmux(cmd, *args, **kwargs)

    def select_layout(self, layout=None):
        """Wrapper for ``$ tmux select-layout <layout>``.

        even-horizontal: Panes are spread out evenly from left to right across
        the window.

        even-vertical: Panes are spread evenly from top to bottom.

        main-horizontal: A large (main) pane is shown at the top of the window
        and the remaining panes are spread from left to right in the leftover
        space at the bottom.

        main-vertical: Similar to main-horizontal but the large pane is placed
        on the left and the others spread from top to bottom along the right.

        tiled: Panes are spread out as evenly as possible over the window in
        both rows and columns.

        custom: custom dimensions (see :term:`tmux(1)` manpages).

        :param layout: string of the layout, 'even-horizontal', 'tiled', etc.
        :type layout: string

        """

        proc = self.tmux(
            'select-layout',
            '-t%s:%s' % (self.get('session_id'), self.get('window_index')),
            layout
        )

        if proc.stderr:
            raise exc.TmuxpException(proc.stderr)

    def set_window_option(self, option, value):
        """Wrapper for ``$ tmux set-window-option <option> <value>``.

        :param value: window value. True/False will turn in 'on' and 'off'.
        :type value: string or bool

        """

        self.server._update_windows()

        if isinstance(value, bool) and value:
            value = 'on'
        elif isinstance(value, bool) and not value:
            value = 'off'

        process = self.tmux(
            'set-window-option',
            '-t%s:%s' % (self.get('session_id'), self.get('window_index')),
            #'-t%s' % self.get('window_id'),
            option, value
        )

        if process.stderr:
            if isinstance(process.stderr, list) and len(process.stderr):
                process.stderr = process.stderr[0]
            raise ValueError(
                'tmux set-window-option -t%s:%s %s %s\n' % (
                    self.get('session_id'),
                    self.get('window_index'),
                    option,
                    value
                ) +
                process.stderr
            )

    def show_window_options(self, option=None, g=False):
        """Return a dict of options for the window.

        For familiarity with tmux, the option ``option`` param forwards to pick
        a single option, forwarding to :meth:`Window.show_window_option`.

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
            return self.show_window_option(option, g=g)
        else:
            tmux_args += ('show-window-options',)
            window_options = self.tmux(
                *tmux_args
            ).stdout

        window_options = [tuple(item.split(' ')) for item in window_options]

        window_options = dict(window_options)

        for key, value in window_options.items():
            if value.isdigit():
                window_options[key] = int(value)

        return window_options

    def show_window_option(self, option, g=False):
        """Return a list of options for the window.

        todo: test and return True/False for on/off string

        :param option: option to return.
        :type option: string
        :param g: Pass ``-g`` flag, global.
        :type g: bool
        :rtype: string, int

        """

        tmux_args = tuple()

        if g:
            tmux_args += ('-g',)

        tmux_args += (option,)

        window_option = self.tmux(
            'show-window-options', *tmux_args
        ).stdout

        if window_option:
            window_option = [tuple(item.split(' '))
                             for item in window_option][0]
        else:
            return None

        if window_option[1].isdigit():
            window_option = (window_option[0], int(window_option[1]))

        return window_option[1]

    def rename_window(self, new_name):
        """Return :class:`Window` object ``$ tmux rename-window <new_name>``.

        :param new_name: name of the window
        :type new_name: string

        """

        import shlex
        lex = shlex.shlex(new_name)
        lex.escape = ' '
        lex.whitespace_split = False

        try:
            self.tmux(
                'rename-window',
                new_name
            )
            self['window_name'] = new_name
        except Exception as e:
            logger.error(e)

        self.server._update_windows()

        return self

    def kill_window(self):
        """Kill the current :class:`Window` object. ``$ tmux kill-window``."""

        proc = self.tmux(
            'kill-window',
            #'-t:%s' % self.get('window_id')
            '-t%s:%s' % (self.get('session_id'), self.get('window_index')),
        )

        if proc.stderr:
            raise exc.TmuxpException(proc.stderr)

        self.server._update_windows()

    def move_window(self, destination):
        """Move the current :class:`Window` object ``$ tmux move-window``.

        :param destination: the ``target window`` or index to move the window
            to.
        :type target_window: string

        """

        proc = self.tmux(
            'move-window',
            '-s%s:%s' % (self.get('session_id'), self.get('window_index')),
            '-t%s:%s' % (self.get('session_id'), destination),
        )

        if proc.stderr:
            raise exc.TmuxpException(proc.stderr)

        self.server._update_windows()

    def select_window(self):
        """Select window. Return ``self``.

        To select a window object asynchrously. If a ``window`` object exists
        and is no longer longer the current window, ``w.select_window()``
        will make ``w`` the current window.

        :rtype: :class:`Window`

        """
        return self.session.select_window(self.get('window_id'))

    def select_pane(self, target_pane):
        """Return selected :class:`Pane` through ``$ tmux select-pane``.

        :param target_pane: ``target_pane``, or ``-U``,``-D``, ``-L``, ``-R``
            or ``-l``.
        :type target_pane: string
        :rtype: :class:`Pane`

        """

        if target_pane in ['-l', '-U', '-D', '-L', '-R']:
            proc = self.tmux(
                'select-pane',
                '-t%s' % self.get('window_id'),
                target_pane
            )
        else:
            proc = self.tmux('select-pane', '-t%s' % target_pane)

        if proc.stderr:
            raise exc.TmuxpException(proc.stderr)

        return self.attached_pane()

    def last_pane(self):
        """Return last pane."""
        return self.select_pane('-l')

    def split_window(self, target=None, attach=True):
        """Split window and return the created :class:`Pane`.

        .. note::

            :term:`tmux(1)` will move window to the new pane if the
            ``split-window`` target is off screen. tmux handles the ``-d`` the
            same way as ``new-window`` and ``attach`` in
            :class:`Session.new_window`.

            By default, this will make the window the pane is created in
            active. To remain on the same window and split the pane in another
            target window, pass in ``attach=False``.


        Used for splitting window and holding in a python object.

        :param attach: make new window the current window after creating it,
                       default True.
        :type attach: bool
        :param target: ``target_pane`` to split.
        :type target: bool

        :rtype: :class:`Pane`

        """

        pformats = ['session_name', 'session_id',
                    'window_index', 'window_id'] + formats.PANE_FORMATS
        tmux_formats = ['#{%s}\t' % f for f in pformats]

        #'-t%s' % self.attached_pane().get('pane_id'),
        # 2013-10-18 LOOK AT THIS, rm'd it..
        tmux_args = tuple()

        if target:
            tmux_args += ('-t%s' % target,)
        else:
            tmux_args += ('-t%s' % self.panes[0].get('pane_id'),)

        tmux_args += (
            '-P', '-F%s' % ''.join(tmux_formats)     # output
        )

        if not attach:
            tmux_args += ('-d',)

        pane = self.tmux(
            'split-window',
            *tmux_args
        )

        # tmux < 1.7. This is added in 1.7.
        if pane.stderr:
            raise exc.TmuxpException(pane.stderr)
            if 'pane too small' in pane.stderr:
                pass

            raise exc.TmuxpException(pane.stderr, self._TMUX, self.panes)
        else:
            pane = pane.stdout[0]

            pane = dict(zip(pformats, pane.split('\t')))

            # clear up empty dict
            pane = dict((k, v) for k, v in pane.items() if v)

        return Pane(window=self, **pane)

    def attached_pane(self):
        """Return the attached :class:`Pane`.

        :rtype: :class:`Pane`

        """
        for pane in self._panes:
            if 'pane_active' in pane:
                # for now pane_active is a unicode
                if pane.get('pane_active') == '1':
                    # return Pane(window=self, **pane)
                    return Pane(window=self, **pane)
                else:
                    continue

        return []

    def _list_panes(self):
        panes = self.server._update_panes()._panes

        panes = [
            p for p in panes if p['session_id'] == self.get('session_id')
        ]
        panes = [
            p for p in panes if p['window_id'] == self.get('window_id')
        ]
        return panes

    @property
    def _panes(self):
        """Property / alias to return :meth:`~._list_panes`."""

        return self._list_panes()

    def list_panes(self):
        """Return list of :class:`Pane` for the window.

        :rtype: list of :class:`Pane`

        """

        return [Pane(window=self, **pane) for pane in self._panes]

    @property
    def panes(self):
        """Property / alias to return :meth:`~.list_panes`."""
        return self.list_panes()
    #: Alias of :attr:`panes`.
    children = panes
