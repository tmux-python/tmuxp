from main import t, SessionNotFound, Session, root_logger
from nose.tools import raises
import unittest
import logging
from random import randint

root_logger.setLevel(logging.INFO)




class TestClass(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1_session_creation(self):

        t.switch_client('tony')

        t.switch_client(TEST_SESSION_NAME)

        assert t.has_session(TEST_SESSION_NAME) is True

    def test_2_has_session_not_found(self):
        assert t.has_session('asdf2314324321') is False

    def test_3_switch_client_returns_session(self):
        '''
        switch_client should return reference to Session object
        '''
        pass

    def test_4_new_session_has_one_window(self):
        self.assertEqual(1, len(session._windows))

    def test_5_session_split_window(self):
        session.attached_window().split_window()

    def test_6_next(self):
        session.attached_window().select_layout('even-horizontal')
        session.attached_window().split_window()
        #session.sync_windows()
        session.attached_window().split_window('-h')

        session.select_window(1)

        session.attached_window().select_pane(1)
        session.attached_pane().send_keys('cd /srv/www/flaskr')
        session.attached_window().select_pane(0)
        session.attached_pane().send_keys('source .env/bin/activate')
        session.new_window('second')
        session.sync_windows()
        self.assertEqual(2, len(session._windows))
        session.new_window('testing 3')
        session.sync_windows()
        self.assertEqual(3, len(session._windows))
        session.select_window(1)
        session.kill_window(target_window='3')
        session.sync_windows()
        self.assertEqual(2, len(session._windows))
        #tmux('display-panes')

    def test_case_2(self):
        pass

    def test_case_3(self):
        pass


if __name__ == '__main__':
    if t.has_clients():

        TEST_SESSION_PREFIX = 'tmxwrp_'

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
            Session.attached_pane().send_keys('created by tmuxwrapper tests.'
                                              ' you may delete this.',
                                              enter=False)
        else:
            t.switch_client(other_sessions[0])

        for session in previous_sessions:
            t.kill_session(previous_sessions)

        TEST_SESSION_NAME = TEST_SESSION_PREFIX + str(randint(0, 1337))

        session = Session.new_session(
            session_name=TEST_SESSION_NAME,
            kill_session=True
        )

        unittest.main()
    else:
        print('must have a tmux client running')
