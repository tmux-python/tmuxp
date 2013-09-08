import unittest
from random import randint
from tmux import t, Session, Window, Pane
from .helpers import TmuxTestCase, TEST_SESSION_PREFIX


class SessionTestCase(TmuxTestCase):
    def test_has_session(self):
        self.assertTrue(t.has_session(self.TEST_SESSION_NAME))
        self.assertFalse(t.has_session('asdf2314324321'))

    def test_new_session(self):
        new_session_name = TEST_SESSION_PREFIX + str(randint(0, 1337))
        new_session = Session.new_session(session_name=new_session_name, detach=True)

        self.assertIsInstance(new_session, Session)

    def test_select_window(self):
        self.assertIsInstance(
            self.session.select_window(1),
            Window
        )

    def test_attached_window(self):
        self.assertIsInstance(
            self.session.attached_window(),
            Window
        )

    def test_attached_pane(self):
        self.assertIsInstance(
            self.session.attached_pane(),
            Pane
        )

    def test_session_rename(self):
        test_name = 'testingdis_sessname'
        self.session.rename_session(test_name)
        self.assertEqual(self.session.get('session_name'), test_name)
        self.session.rename_session(self.TEST_SESSION_NAME)
        self.assertEqual(self.session.get('session_name'), self.TEST_SESSION_NAME)


if __name__ == '__main__':
    unittest.main()
