import unittest
from random import randint
from time import sleep
from .. import t, Session, Window, Pane
from ..util import tmux
from .helpers import TmuxTestCase, TEST_SESSION_PREFIX


class SessionTestCase(TmuxTestCase):
    def test_has_session(self):
        self.assertTrue(t.has_session(self.TEST_SESSION_NAME))
        self.assertFalse(t.has_session('asdf2314324321'))

    def test_select_window(self):
        self.assertEqual(len(self.session._windows), 1)
        window_base_index = int(self.session.attached_window().get('window_index'))

        self.assertEqual(len(self.session.list_windows()), 1)
        self.assertIsInstance(self.session.select_window(window_base_index), Window)

    def test_attached_window(self):
        self.assertIsInstance(self.session.attached_window(), Window)

    def test_attached_pane(self):
        self.assertIsInstance(self.session.attached_pane(), Pane)

    def test_session_rename(self):
        test_name = 'testingdis_sessname'
        self.session.rename_session(test_name)
        self.assertEqual(self.session.get('session_name'), test_name)
        self.session.rename_session(self.TEST_SESSION_NAME)
        self.assertEqual(self.session.get('session_name'), self.TEST_SESSION_NAME)


class SessionCleanTestCase(TmuxTestCase):
    @unittest.skip("not working yet")
    def test_is_session_clean(self):
        self.assertEqual(self.session.is_clean(), True)
        self.session.attached_window().attached_pane().send_keys('top')
        sleep(.4)
        self.session.attached_window().list_panes()
        self.session.attached_window().attached_pane().send_keys('C-c', enter=False)
        self.assertEqual(self.session.is_clean(), False)


class SessionNewTestCase(TmuxTestCase):
    def test_new_session(self):
        new_session_name = TEST_SESSION_PREFIX + str(randint(0, 1337))
        new_session = t.new_session(session_name=new_session_name, detach=True)

        self.assertIsInstance(new_session, Session)

if __name__ == '__main__':
    unittest.main()
