# -*- coding: utf8 - *-
"""
    tmuxp.util
    ~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
from __future__ import absolute_import, division, print_function, with_statement

from functools import wraps
import unittest
import collections
import subprocess
import os

from . import log
import logging

logger = logging.getLogger(__name__)


class tmux(object):
    ''':py:mod:`subprocess` for :term:`tmux(1)`.

    Usage:

    .. code-block:: python

        tmux('new-session', '-s%' % 'my session')

    Equivalent to:

    .. code-block:: bash

        $ tmux new-session -s my session
    '''

    def __init__(self, *args, **kwargs):
        cmd = ['tmux']
        cmd += args  # add the command arguments to cmd
        cmd = [str(c) for c in cmd]

        self.cmd = cmd

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.process.wait()
            stdout, stderr = self.process.stdout.read(), self.process.stderr.read()
        except Exception as e:
            logger.error('Exception for %s: \n%s' % (
                cmd,
                e.message)
            )
        self.stdout = stdout.split('\n')
        self.stdout = filter(None, self.stdout)  # filter empty values

        self.stderr = stderr.split('\n')
        self.stderr = filter(None, self.stderr)  # filter empty values

        if 'has-session' in cmd and len(self.stderr):
            if not self.stdout:
                self.stdout = self.stderr[0]

        logging.debug('self.stdout for %s: \n%s' % (' '.join(cmd), self.stdout))


class TmuxMappingObject(collections.MutableMapping):
    '''
    Base: :py:class:`collections.MutableMapping`

    Convenience container. Base class for :class:`Pane`, :class:`Window`,
    :class:`Session` and :class:`Server`.

    Instance attributes for useful information :term:`tmux(1)` uses for
    Session, Window, Pane, stored :attr:`self._TMUX`. For example, a
    :class:`Window` will have a ``window_id`` and ``window_name``.
    '''

    def __getitem__(self, key):
        return self._TMUX[key]

    def __setitem__(self, key, value):
        self._TMUX[key] = value
        self.dirty = True

    def __delitem__(self, key):
        del self._TMUX[key]
        self.dirty = True

    def keys(self):
        return self._TMUX.keys()

    def __iter__(self):
        return self._TMUX.__iter__()

    def __len__(self):
        return len(self._TMUX.keys())


class TmuxRelationalObject(object):
    '''
    Manages collection of child objects  (a :class:`Server` has a collection of
    :class:`Session` objects, a :class:`Session` has collection of
    :class:`Window`)

    Children of :class:`TmuxRelationalObject` are going to have a
    ``self.children``, ``self.childIdAttribute`` and ``self.list_children``.

    ================ ================== ===================== ============================
    Object           ``.children``      ``.childIdAttribute`` ``.list_children``
    ================ ================== ===================== ============================
    :class:`Server`  ``self._sessions`` 'session_id'          :meth:`Server.list_sessions`
    :class:`Session` ``self._windows``  'window_id'           :meth:`Session.list_windows`
    :class:`Window`  ``self._panes``    'pane_id'             :meth:`Window.list_panes`
    :class:`Pane`
    ================ ================== ===================== ============================

    '''

    def findWhere(self, attrs):
        ''' find first match

        Based on `.findWhere()`_ from `underscore.js`_.

        .. _.findWhere(): http://underscorejs.org/#findWhere
        .. _underscore.js: http://underscorejs.org/

        '''
        return self.where(attrs, True)

    def where(self, attrs, first=False):
        ''' find child objects by properties

        Based on `.where()`_ from `underscore.js`_.

        .. _.where(): http://underscorejs.org/#where
        .. _underscore.js: http://underscorejs.org/

        :param attrs: tmux properties to match
        :type attrs: dict
        :rtype: list
        '''

        # from https://github.com/serkanyersen/underscore.py
        def by(val, *args):
            for key, value in attrs.items():
                try:
                    if attrs[key] != val[key]:
                        return False
                except KeyError:
                    return False
                return True

        if first:
            return list(filter(by, self.children))[0]
        else:
            return list(filter(by, self.children))

    def getById(self, id):
        '''
        Based on `.get()`_ from `backbone.js`_.

        .. _backbone.js: http://backbonejs.org/
        .. _.get(): http://backbonejs.org/#Collection-get

        :param id:
        :type id: string
        :rtype: object
        '''
        for child in self.list_children():
            if child[self.childIdAttribute] == id:
                return child
            else:
                continue

        return None


def which(exe=None):
    '''
    Python clone of /usr/bin/which

    from salt.util - https://www.github.com/saltstack/salt - license apache
    '''
    if exe:
        if os.access(exe, os.X_OK):
            return exe

        # default path based on busybox's default
        default_path = '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin'
        search_path = os.environ.get('PATH', default_path)

        for path in search_path.split(os.pathsep):
            full_path = os.path.join(path, exe)
            if os.access(full_path, os.X_OK):
                return full_path
        log.trace(
            '{0!r} could not be found in the following search '
            'path: {1!r}'.format(
                exe, search_path
            )
        )
    log.trace('No executable was passed to be searched by which')
    return None
