import unittest
from random import randint
from .. import t, Session, Window, Pane
from .helpers import TmuxTestCase, TEST_SESSION_PREFIX


class SessionTestCase(TmuxTestCase):
    def test_has_session(self):
        self.assertTrue(t.has_session(self.TEST_SESSION_NAME))
        self.assertFalse(t.has_session('asdf2314324321'))

    def test_new_session(self):
        new_session_name = TEST_SESSION_PREFIX + str(randint(0, 1337))
        new_session = Session.new_session(session_name=new_session_name)

        self.assertIsInstance(new_session, Session)

    def test_select_window(self):
        self.assertIsInstance(self.session.select_window(1), Window)

    def test_attached_window(self):
        self.assertIsInstance(self.session.attached_window(), Window)

    def test_attached_pane(self):
        self.assertIsInstance(self.session.attached_pane(), Pane)

if __name__ == '__main__':
    unittest.main()
