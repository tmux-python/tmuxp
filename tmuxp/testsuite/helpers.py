import unittest
from random import randint
from ..util import tmux
from .. import t, Server
from ..logxtreme import root_logger, logging
from ..exc import TmuxNoClientsRunning, ErrorReturnCode_1


TEST_SESSION_PREFIX = 'tmuxp_'
root_logger.setLevel(logging.ERROR)

def ho(line, stdin, process):
    pass

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
    if not t.server_exists():
        t.client = tmux('-C', _out=ho)
    if not t.has_clients():
        t.client = tmux('-C', _out=ho)

    session_list = t.list_sessions()
    # find current sessions prefixed with tmuxp
    previous_sessions = [s.session_name for s in session_list
                            if s.session_name.startswith(TEST_SESSION_PREFIX)]

    other_sessions = [s.session_name for s in session_list
                        if not s.session_name.startswith(
                            TEST_SESSION_PREFIX
                        )]

    if not other_sessions:
        # create a test session so client won't close when other windows
        # cleaned up
        t.new_session(session_name='test_' + str(randint(0, 1337)))
        #Session.attached_pane().send_keys('created by tmuxp tests.'
        #                                  ' you may delete this.',
        #                                  enter=False)
    else:
        t.switch_client(other_sessions[0])

    for session in previous_sessions:
        logging.debug('Old test test session %s found. Killing it.' % session)
        t.kill_session(session)

    TEST_SESSION_NAME = TEST_SESSION_PREFIX + str(randint(0, 13370))

    session = t.new_session(
        session_name=TEST_SESSION_NAME,
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

    done = False
    client = None

    def hi(self, line, stdin, process):
        if self.done:
            process.kill()
            return True

    def setup(self):
        pass

    @classmethod
    def setUpClass(cls):
        try:
            # bootstrap() retyrns a tuple  of session and the session object
            cls.TEST_SESSION_NAME, cls.session = bootstrap()
        except TmuxNoClientsRunning:
            #def ho(line, stdin, process):
            #    return cls.hi(cls, line, stdin, process)
            logging.error('test: TmuxNoClientsRunning')
            #cls.client = tmux('-C', _out=ho)
            cls.TEST_SESSION_NAME, cls.session = bootstrap()
        except Exception as e:
            #cls.tearDownClass()
            logging.error(e)
            #cls.fail()
            #import ipdb
            #ipdb.set_trace()
            import traceback

            logging.error(traceback.print_exc())
            raise Exception(e)
        return

    @classmethod
    def tearDownClass(cls):
        #cls.done = True
        if cls.client:
            cls.client.terminate()
        #if t.client:
        #   cls.client.terminate()
        #t.list_sessions()
