from .helpers import TestTmux
from tmux import Pane
import unittest


class TestWindowSelect(TestTmux):
    def test_select_window(self):
        self.session.new_window('testing 3')
        self.session.select_window(2)
        self.assertEqual(2, int(self.session.attached_window().get('window_index')))


class TestWindowCreation(TestTmux):

    def test_sync_windows(self):
        #self.session.select_window(1)
        current_windows = len(self.session._windows)
        self.session.attached_window().select_pane(1)
        self.session.attached_pane().send_keys('cd /srv/www/flaskr')
        self.session.attached_window().select_pane(0)
        self.session.attached_pane().send_keys('source .env/bin/activate')
        self.session.new_window('second')
        current_windows += 1
        self.assertEqual(current_windows, len(self.session._windows))
        self.session.new_window(3)
        current_windows += 1
        self.assertEqual(current_windows, len(self.session._windows))
        self.session.select_window(1)
        self.session.kill_window(target_window=3)
        current_windows -= 1
        self.assertEqual(current_windows, len(self.session._windows))
        #tmux('display-panes')

    def test_sync_panes(self):
        self.session.select_window(1)

        self.assertEqual(1, len(self.session.attached_window()._panes))
        self.session.attached_window().select_layout('even-horizontal')

        self.session.attached_window().split_window()
        self.assertEqual(2, len(self.session.attached_window()._panes))
        self.session.attached_window().split_window('-h')
        self.assertEqual(3, len(self.session.attached_window()._panes))

    def test_attached_pane(self):
        self.assertIsInstance(self.session.attached_window().attached_pane(), Pane)

    def test_split_window(self):
        window_name = 'test split window'
        window = self.session.new_window(window_name=window_name)
        pane = window.split_window()
        self.assertEqual(2, len(self.session.attached_window()._panes))
        self.assertIsInstance(
            pane, Pane
        )

        self.assertEqual(2, len(window._panes))


if __name__ == '__main__':
    unittest.main()
