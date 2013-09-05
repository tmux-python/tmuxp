# -*- coding: utf-8 -*-
"""
    tmuxwrapper.tests
    ~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2013 Tony Narlock <tony@git-pull.com>.
    :license: BSD, see LICENSE for details

    this can be ran like::

        nosetests tests.py

    or::

        python tests.py

    also, if you have ``node`` and ``npm`` you may (sudo)::

        ``npm install -g nodemon``
        ``nodemon --watch tests.py --watch main.py --exec "nosetests" tests.py

    or::

        ``nodemon --watch tests.py --watch main.py --exec "python" tests.py

    These tests require an active tmux client open while it runs. It is best to
    have a second terminal with tmux running alongside the terminal running the
    tests.
"""

from nose.tools import raises
import unittest
from random import randint
from sh import ErrorReturnCode_1
from tmux import Session, t
from tmux.logxtreme import root_logger, logging
from tmux.exc import SessionNotFound


# set logging to INFO level
root_logger.setLevel(logging.ERROR)
TEST_SESSION_PREFIX = 'tmxwrp_'


def bootstrap():
    '''
        Returns a tuple of the session_name (generated) and a :class:`Session`

        Checks to verify if the user has a tmux client open.

        It will clean up and delete other sessions starting with the
        TEST_SESSION_PREFIX ``tmxwrap``.

        Since tmux closes when all sessions are deleted, the bootstrap will see
        if there is no other client open aside from a tmuxwrp_ prefixed session
        a dumby session will be made to prevent tmux from closing.

    '''
    if t.has_clients():

        # find current sessions prefixed with tmxwrp
        previous_sessions = [s.session_name for s in t.list_sessions()
                             if s.session_name.startswith(TEST_SESSION_PREFIX)]

        other_sessions = [s.session_name for s in t.list_sessions()
                          if not s.session_name.startswith(
                              TEST_SESSION_PREFIX
                          )]

        if not other_sessions:
            # create a test session so client won't close when other windows
            # cleaned up
            Session.new_session(session_name='test_' + str(randint(0, 1337)))
            #Session.attached_pane().send_keys('created by tmuxwrapper tests.'
            #                                  ' you may delete this.',
            #                                  enter=False)
        else:
            t.switch_client(other_sessions[0])

        for session in previous_sessions:
            logging.debug(session)
            t.kill_session(session)

        TEST_SESSION_NAME = TEST_SESSION_PREFIX + str(randint(0, 1337))

        session = Session.new_session(
            session_name=TEST_SESSION_NAME,
            #kill_session=True
        )

        t.switch_client(TEST_SESSION_NAME)

        return (TEST_SESSION_NAME, session)


class TestTmux(unittest.TestCase):
    '''
        self.session
            Session object
        self.TEST_SESSION_NAME
            string. name of the test case session.
    '''

    def setup(self):
        pass
        #t.list_sessions()

    @classmethod
    def setUpClass(cls):
        try:
            # bootstrap() retyrns a tuple  of session and the session object
            cls.TEST_SESSION_NAME, cls.session = bootstrap()
        except Exception as e:
            cls.tearDownClass()
            logging.error(e)
            raise e
        return

    @classmethod
    def tearDownClass(cls):
        t.list_sessions()


def main():
    if t.has_clients():
        #unittest.main()
        suites = unittest.TestLoader().discover(".", pattern="*.py")

        def suite():
            suite = unittest.TestSuite()
            for other_suite in suites:
                suite.addTest(other_suite)

            return suite
        unittest.TextTestRunner().run(suite())
    else:
        print('must have a tmux client running')

if __name__ == '__main__':
    main()
