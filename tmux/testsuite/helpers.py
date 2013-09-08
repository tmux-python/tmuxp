import unittest
from tmux import t, Session
from sh import ErrorReturnCode_1
from tmux.logxtreme import root_logger, logging
from tmux.exc import SessionNotFound
from random import randint
import unittest


TEST_SESSION_PREFIX = 'tmuxp_'
root_logger.setLevel(logging.ERROR)


def bootstrap():
    '''
        Returns a tuple of the session_name (generated) and a :class:`Session`

        Checks to verify if the user has a tmux client open.

        It will clean up and delete other sessions starting with the
        :attr:`TEST_SESSION_PREFIX` ``tmuxp``.

        Since tmux closes when all sessions are deleted, the bootstrap will see
        if there is no other client open aside from a tmuxp_ prefixed session
        a dumby session will be made to prevent tmux from closing.

    '''
    if t.has_clients():

        # find current sessions prefixed with tmuxp
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
            #Session.attached_pane().send_keys('created by tmuxp tests.'
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


class TmuxTestCase(unittest.TestCase):
    '''
        self.session
            Session object
        self.TEST_SESSION_NAME
            string. name of the test case session.
    '''

    def setup(self):
        pass

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
