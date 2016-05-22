# -*- coding: utf-8 -*-
"""Helper methods for tmuxp unittests.

_CallableContext, WhateverIO, decorator and stdouts are from the case project,
https://github.com/celery/case, license BSD 3-clause.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import contextlib
import functools
import inspect
import io
import logging
import os
import sys
import tempfile
from contextlib import contextmanager

from tmuxp import exc
from tmuxp.server import Server

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

logger = logging.getLogger(__name__)

TEST_SESSION_PREFIX = 'test tmuxp_'

namer = tempfile._RandomNameSequence()
current_dir = os.path.abspath(os.path.dirname(__file__))
example_dir = os.path.abspath(os.path.join(current_dir, '..', 'examples'))
fixtures_dir = os.path.realpath(os.path.join(current_dir, 'fixtures'))


def get_test_session_name(server, prefix=TEST_SESSION_PREFIX):
    while True:
        session_name = prefix + next(namer)
        if not server.has_session(session_name):
            break
    return session_name


def get_test_window_name(session, prefix=TEST_SESSION_PREFIX):
    while True:
        window_name = prefix + next(namer)
        if not session.findWhere(window_name=window_name):
            break
    return window_name


@contextlib.contextmanager
def temp_session(server, *args, **kwargs):
    """Return a context manager with a temporary session.

    e.g.::

        with temp_session(server) as session:
            session.new_window(window_name='my window')

    The session will destroy itself upon closing with :meth:`Session.
    kill_session()`.

    If no ``session_name`` is entered, :func:`get_test_session_name` will make
    an unused session name.

    :args: Same arguments as :meth:`Server.new_session`
    :yields: Temporary session
    :rtype: :class:`Session`
    """

    if 'session_name' in kwargs:
        session_name = kwargs.pop('session_name')
    else:
        session_name = get_test_session_name(server)

    session = server.new_session(session_name, *args, **kwargs)

    try:
        yield session
    finally:
        if server.has_session(session_name):
            session.kill_session()
    return


@contextlib.contextmanager
def temp_window(session, *args, **kwargs):
    """Return a context manager with a temporary window.

    e.g.::

        with temp_window(session) as window:
            my_pane = window.split_window()

    The window will destroy itself upon closing with :meth:`window.
    kill_window()`.

    If no ``window_name`` is entered, :func:`get_test_window_name` will make
    an unused window name.

    :args: Same arguments as :meth:`Session.new_window`
    :yields: Temporary window
    :rtype: :class:`Window`
    """

    if 'window_name' not in kwargs:
        window_name = get_test_window_name(session)
    else:
        window_name = kwargs.pop('window_name')

    window = session.new_window(window_name, *args, **kwargs)

    # Get ``window_id`` before returning it, it may be killed within context.
    window_id = window.get('window_id')

    try:
        yield session
    finally:
        if session.findWhere(window_id=window_id):
            window.kill_window()
    return


class TestCase(unittest.TestCase):

    """Base TestClass so we don't have to try: unittest2 every module. """

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()  # for python 2.6 unittest2


class TmuxTestCase(TestCase):

    """TmuxTestCase class, wraps the TestCase in a :class:`Session`."""

    #: :class:`Session` object.
    session = None
    #: Session name for the TestCase.
    TEST_SESSION_NAME = None

    def temp_session(self, session_name=None):
        return temp_session(self.server, session_name)

    def setUp(self):
        """Run bootstrap if :attr:`~.session` is not set."""

        if not self.TEST_SESSION_NAME or not self.session:
            self.bootstrap()

    def bootstrap(self):
        """Return tuple of the session_name (generated) and :class:`Session`.

        Checks to verify if the user has a tmux client open.

        It will clean up and delete other sessions starting with the
        :attr:`TEST_SESSION_PREFIX` ``tmuxp``.

        Since tmux closes when all sessions are deleted, the bootstrap will see
        if there is no other client open aside from a tmuxp_ prefixed session
        a dumby session will be made to prevent tmux from closing.

        """
        self.t = t = Server()
        t.socket_name = 'tmuxp_test'

        session_name = 'tmuxp'
        if not t.has_session(session_name):
            t.cmd('new-session', '-d', '-s', session_name)

        # find current sessions prefixed with tmuxp
        old_test_sessions = [
            s.get('session_name') for s in t._sessions
            if s.get('session_name').startswith(TEST_SESSION_PREFIX)
        ]

        TEST_SESSION_NAME = get_test_session_name(server=t)

        try:
            session = t.new_session(
                session_name=TEST_SESSION_NAME,
            )
        except exc.TmuxpException as e:
            raise e

        """
        Make sure that tmuxp can :ref:`test_builder_visually` and switches to
        the newly created session for that testcase.
        """
        try:
            t.switch_client(session.get('session_id'))
            pass
        except exc.TmuxpException as e:
            # t.attach_session(session.get('session_id'))
            pass

        for old_test_session in old_test_sessions:
            logger.debug(
                'Old test test session %s found. Killing it.' %
                old_test_session
            )
            t.kill_session(old_test_session)
        assert TEST_SESSION_NAME == session.get('session_name')
        assert TEST_SESSION_NAME != 'tmuxp'

        self.TEST_SESSION_NAME = TEST_SESSION_NAME
        self.server = t
        self.session = session


StringIO = io.StringIO
_SIO_write = StringIO.write
_SIO_init = StringIO.__init__


def update_wrapper(wrapper, wrapped, *args, **kwargs):
    wrapper = functools.update_wrapper(wrapper, wrapped, *args, **kwargs)
    wrapper.__wrapped__ = wrapped
    return wrapper


def wraps(wrapped,
          assigned=functools.WRAPPER_ASSIGNMENTS,
          updated=functools.WRAPPER_UPDATES):
    return functools.partial(update_wrapper, wrapped=wrapped,
                             assigned=assigned, updated=updated)


class _CallableContext(object):

    def __init__(self, context, cargs, ckwargs, fun):
        self.context = context
        self.cargs = cargs
        self.ckwargs = ckwargs
        self.fun = fun

    def __call__(self, *args, **kwargs):
        return self.fun(*args, **kwargs)

    def __enter__(self):
        self.ctx = self.context(*self.cargs, **self.ckwargs)
        return self.ctx.__enter__()

    def __exit__(self, *einfo):
        if self.ctx:
            return self.ctx.__exit__(*einfo)


def decorator(predicate):
    context = contextmanager(predicate)

    @wraps(predicate)
    def take_arguments(*pargs, **pkwargs):

        @wraps(predicate)
        def decorator(cls):
            if inspect.isclass(cls):
                orig_setup = cls.setUp
                orig_teardown = cls.tearDown

                @wraps(cls.setUp)
                def around_setup(*args, **kwargs):
                    try:
                        contexts = args[0].__rb3dc_contexts__
                    except AttributeError:
                        contexts = args[0].__rb3dc_contexts__ = []
                    p = context(*pargs, **pkwargs)
                    p.__enter__()
                    contexts.append(p)
                    return orig_setup(*args, **kwargs)
                around_setup.__wrapped__ = cls.setUp
                cls.setUp = around_setup

                @wraps(cls.tearDown)
                def around_teardown(*args, **kwargs):
                    try:
                        contexts = args[0].__rb3dc_contexts__
                    except AttributeError:
                        pass
                    else:
                        for context in contexts:
                            context.__exit__(*sys.exc_info())
                    orig_teardown(*args, **kwargs)
                around_teardown.__wrapped__ = cls.tearDown
                cls.tearDown = around_teardown

                return cls
            else:
                @wraps(cls)
                def around_case(self, *args, **kwargs):
                    with context(*pargs, **pkwargs) as context_args:
                        context_args = context_args or ()
                        if not isinstance(context_args, tuple):
                            context_args = (context_args,)
                        return cls(*(self,) + args + context_args, **kwargs)
                return around_case

        if len(pargs) == 1 and callable(pargs[0]):
            fun, pargs = pargs[0], ()
            return decorator(fun)
        return _CallableContext(context, pargs, pkwargs, decorator)
    assert take_arguments.__wrapped__
    return take_arguments


class WhateverIO(StringIO):

    def __init__(self, v=None, *a, **kw):
        _SIO_init(self, v.decode() if isinstance(v, bytes) else v, *a, **kw)

    def write(self, data):
        _SIO_write(self, data.decode() if isinstance(data, bytes) else data)


@decorator
def stdouts():
    """Override `sys.stdout` and `sys.stderr` with `StringIO`
    instances.
    Decorator example::
        @mock.stdouts
        def test_foo(self, stdout, stderr):
            something()
            self.assertIn('foo', stdout.getvalue())
    Context example::
        with mock.stdouts() as (stdout, stderr):
            something()
            self.assertIn('foo', stdout.getvalue())
    """
    prev_out, prev_err = sys.stdout, sys.stderr
    prev_rout, prev_rerr = sys.__stdout__, sys.__stderr__
    mystdout, mystderr = WhateverIO(), WhateverIO()
    sys.stdout = sys.__stdout__ = mystdout
    sys.stderr = sys.__stderr__ = mystderr

    try:
        yield mystdout, mystderr
    finally:
        sys.stdout = prev_out
        sys.stderr = prev_err
        sys.__stdout__ = prev_rout
        sys.__stderr__ = prev_rerr


@decorator
def mute():
    """Redirect `sys.stdout` and `sys.stderr` to /dev/null, silencent them.
    Decorator example::
        @mute
        def test_foo(self):
            something()
    Context example::
        with mute():
            something()
    """
    prev_out, prev_err = sys.stdout, sys.stderr
    prev_rout, prev_rerr = sys.__stdout__, sys.__stderr__
    devnull = open(os.devnull, 'w')
    mystdout, mystderr = devnull, devnull
    sys.stdout = sys.__stdout__ = mystdout
    sys.stderr = sys.__stderr__ = mystderr

    try:
        yield
    finally:
        sys.stdout = prev_out
        sys.stderr = prev_err
        sys.__stdout__ = prev_rout
        sys.__stderr__ = prev_rerr


class EnvironmentVarGuard(object):

    """Class to help protect the environment variable properly.  Can be used as
    a context manager.
      Vendorize to fix issue with Anaconda Python 2 not
      including test module, see #121.
    """

    def __init__(self):
        self._environ = os.environ
        self._unset = set()
        self._reset = dict()

    def set(self, envvar, value):
        if envvar not in self._environ:
            self._unset.add(envvar)
        else:
            self._reset[envvar] = self._environ[envvar]
        self._environ[envvar] = value

    def unset(self, envvar):
        if envvar in self._environ:
            self._reset[envvar] = self._environ[envvar]
            del self._environ[envvar]

    def __enter__(self):
        return self

    def __exit__(self, *ignore_exc):
        for envvar, value in self._reset.items():
            self._environ[envvar] = value
        for unset in self._unset:
            del self._environ[unset]
