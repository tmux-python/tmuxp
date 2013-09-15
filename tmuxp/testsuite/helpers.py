import unittest
import time
from random import randint
from .. import t, Server
from ..logxtreme import root_logger, logging
from ..exc import TmuxNoClientsRunning, ErrorReturnCode_1

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

    session_list = t.list_sessions()

    assert session_list == t.list_sessions()

    # find current sessions prefixed with tmuxp
    old_test_sessions = [s.get('session_name') for s in session_list
                        if s.get('session_name').startswith(TEST_SESSION_PREFIX)]

    other_sessions = [s.get('session_name') for s in session_list
                      if not s.get('session_name').startswith(
                          TEST_SESSION_PREFIX
                      )]

    assert session_list == t.list_sessions()

    TEST_SESSION_NAME = TEST_SESSION_PREFIX + str(randint(0, 13370))
    session = t.new_session(
        session_name=TEST_SESSION_NAME,
    )

    for old_test_session in old_test_sessions:
        logging.debug('Old test test session %s found. Killing it.' %
                      old_test_session)
        t.kill_session(old_test_session)

    assert TEST_SESSION_NAME == session.get('session_name')

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
            cls.TEST_SESSION_NAME, cls.session = bootstrap()
        except TmuxNoClientsRunning:
            logging.error('test: TmuxNoClientsRunning')
            cls.TEST_SESSION_NAME, cls.session = bootstrap()
        except Exception as e:
            import traceback
            logging.error(e)

            logging.error(traceback.print_exc())
            #raise Exception(e)
        return

    @classmethod
    def tearDownClass(cls):
        pass
