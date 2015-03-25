# -*- coding: utf-8 -*-
"""Utility and helper methods for tmuxp.

tmuxp.util
~~~~~~~~~~

"""
from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import unittest
import collections
import subprocess
import re
import os
import sys
import shlex
import logging

from distutils.version import StrictVersion

from . import exc

from ._compat import console_to_str

logger = logging.getLogger(__name__)

PY2 = sys.version_info[0] == 2


def run_before_script(script_file):
    """Function to wrap try/except for subprocess.check_call()."""
    try:
        proc = subprocess.Popen(
            shlex.split(str(script_file)),
            stderr=subprocess.PIPE
        )
        proc.wait()

        if proc.returncode:
            stderr = proc.stderr.read()
            proc.stderr.close()
            stderr = console_to_str(stderr).split('\n')
            stderr = '\n'.join(list(filter(None, stderr)))  # filter empty values

            raise exc.BeforeLoadScriptError(proc.returncode, os.path.abspath(script_file), stderr)

        return proc.returncode
    except OSError as e:
        if e.errno == 2:
            raise exc.BeforeLoadScriptNotExists(e, os.path.abspath(script_file))
        else:
            raise(e)


class tmux(object):

    """:py:mod:`subprocess` for :term:`tmux(1)`.

    Usage::

        proc = tmux('new-session', '-s%' % 'my session')

        if proc.stderr:
            raise exc.TmuxpException(
                'Command: %s returned error: %s' % (proc.cmd, proc.stderr)
            )

        print('tmux command returned %s' % proc.stdout)

    Equivalent to:

    .. code-block:: bash

        $ tmux new-session -s my session

    """

    def __init__(self, *args, **kwargs):
        cmd = [which('tmux')]
        cmd += args  # add the command arguments to cmd
        cmd = [str(c) for c in cmd]

        self.cmd = cmd

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.process.wait()
            stdout = self.process.stdout.read()
            self.process.stdout.close()
            stderr = self.process.stderr.read()
            self.process.stderr.close()
        except Exception as e:
            logger.error(
                'Exception for %s: \n%s' % (
                    subprocess.list2cmdline(cmd),
                    e
                )
            )

        self.stdout = console_to_str(stdout)
        self.stdout = self.stdout.split('\n')
        self.stdout = list(filter(None, self.stdout))  # filter empty values

        self.stderr = console_to_str(stderr)
        self.stderr = self.stderr.split('\n')
        self.stderr = list(filter(None, self.stderr))  # filter empty values

        if 'has-session' in cmd and len(self.stderr):
            if not self.stdout:
                self.stdout = self.stderr[0]

        logging.debug('self.stdout for %s: \n%s' %
                      (' '.join(cmd), self.stdout))


class TmuxMappingObject(collections.MutableMapping):

    """Base: :py:class:`collections.MutableMapping`.

    Convenience container. Base class for :class:`Pane`, :class:`Window`,
    :class:`Session` and :class:`Server`.

    Instance attributes for useful information :term:`tmux(1)` uses for
    Session, Window, Pane, stored :attr:`self._TMUX`. For example, a
    :class:`Window` will have a ``window_id`` and ``window_name``.

    """

    def __getitem__(self, key):
        return self._TMUX[key]

    def __setitem__(self, key, value):
        self._TMUX[key] = value
        self.dirty = True

    def __delitem__(self, key):
        del self._TMUX[key]
        self.dirty = True

    def keys(self):
        """Return list of keys."""
        return self._TMUX.keys()

    def __iter__(self):
        return self._TMUX.__iter__()

    def __len__(self):
        return len(self._TMUX.keys())


class TmuxRelationalObject(object):

    """Base Class for managing tmux object child entities.

    Manages collection of child objects  (a :class:`Server` has a collection of
    :class:`Session` objects, a :class:`Session` has collection of
    :class:`Window`)

    Children of :class:`TmuxRelationalObject` are going to have a
    ``self.children``, ``self.childIdAttribute`` and ``self.list_children``.

    ================ ================== ===================== ============================
    Object           ``.children``      ``.childIdAttribute`` method
    ================ ================== ===================== ============================
    :class:`Server`  ``self._sessions`` 'session_id'          :meth:`Server.list_sessions`
    :class:`Session` ``self._windows``  'window_id'           :meth:`Session.list_windows`
    :class:`Window`  ``self._panes``    'pane_id'             :meth:`Window.list_panes`
    :class:`Pane`
    ================ ================== ===================== ============================

    """

    def findWhere(self, attrs):
        """Return object on first match.

        Based on `.findWhere()`_ from `underscore.js`_.

        .. _.findWhere(): http://underscorejs.org/#findWhere
        .. _underscore.js: http://underscorejs.org/

        """
        try:
            return self.where(attrs)[0]
        except IndexError:
            return None

    def where(self, attrs, first=False):
        """Return objects matching child objects properties.

        Based on `.where()`_ from `underscore.js`_.

        .. _.where(): http://underscorejs.org/#where
        .. _underscore.js: http://underscorejs.org/

        :param attrs: tmux properties to match
        :type attrs: dict
        :rtype: list

        """

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
        """Return object based on ``childIdAttribute``.

        Based on `.get()`_ from `backbone.js`_.

        .. _backbone.js: http://backbonejs.org/
        .. _.get(): http://backbonejs.org/#Collection-get

        :param id:
        :type id: string
        :rtype: object

        """
        for child in self.children:
            if child[self.childIdAttribute] == id:
                return child
            else:
                continue

        return None


def which(exe=None):
    """Return path of bin. Python clone of /usr/bin/which.

    from salt.util - https://www.github.com/saltstack/salt - license apache

    :param exe: Application to search PATHs for.
    :type exe: string
    :rtype: string

    """
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
        raise exc.TmuxpException(
            '{0!r} could not be found in the following search '
            'path: {1!r}'.format(
                exe, search_path
            )
        )
    logger.error('No executable was passed to be searched by which')
    return None


def is_version(version):
    """Return True if tmux version installed.

    :param version: version, '1.8'
    :param type: string
    :rtype: bool

    """
    proc = tmux('-V')

    if proc.stderr:
        raise exc.TmuxpException(proc.stderr)

    installed_version = proc.stdout[0].split('tmux ')[1]

    return StrictVersion(installed_version) == StrictVersion(version)


def has_required_tmux_version(version=None):
    """Return if tmux meets version requirement. Version >1.8 or above.

    :versionchanged: 0.1.7
        Versions will now remove trailing letters per `Issue 55`_.

        .. _Issue 55: https://github.com/tony/tmuxp/issues/55.

    """

    if not version:
        proc = tmux('-V')

        if proc.stderr:
            if proc.stderr[0] == 'tmux: unknown option -- V':
                raise exc.TmuxpException(
                    'tmuxp supports tmux 1.8 and greater. This system'
                    ' is running tmux 1.3 or earlier.')
            raise exc.TmuxpException(proc.stderr)

        version = proc.stdout[0].split('tmux ')[1]

    version = re.sub(r'[a-z]', '', version)

    if StrictVersion(version) <= StrictVersion("1.7"):
        raise exc.TmuxpException(
            'tmuxp only supports tmux 1.8 and greater. This system'
            ' has %s installed. Upgrade your tmux to use tmuxp.' % version
        )
    return version


def oh_my_zsh_auto_title():
    """Give warning and offer to fix ``DISABLE_AUTO_TITLE``.

    see: https://github.com/robbyrussell/oh-my-zsh/pull/257

    """

    if 'SHELL' in os.environ and 'zsh' in os.environ.get('SHELL'):
        if os.path.exists(os.path.expanduser('~/.oh-my-zsh')):
            # oh-my-zsh exists
            if (
                'DISABLE_AUTO_TITLE' not in os.environ or
                os.environ.get('DISABLE_AUTO_TITLE') == "false"
            ):
                print('Please set:\n\n'
                      '\texport DISABLE_AUTO_TITLE = \'true\'\n\n'
                      'in ~/.zshrc or where your zsh profile is stored.\n'
                      'Remember the "export" at the beginning!\n\n'
                      'Then create a new shell or type:\n\n'
                      '\t$ source ~/.zshrc')
