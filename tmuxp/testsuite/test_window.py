import unittest
from .. import Pane, t
from ..util import tmux
from ..exc import TmuxSessionNotFound
from .helpers import TmuxTestCase
from ..logxtreme import logging


class WindowSelectTestCase(TmuxTestCase):

    def test_select_window(self):
        logging.info(self.session.list_windows())
        logging.info(self.session.list_windows())
        logging.info(t.list_sessions())
        try:
            logging.info(tmux('list_clients'))
        except Exeption:
            pass
        logging.info(self.session._TMUX)
        window_count = len(self.session.list_windows())
        self.assertEqual(window_count, 1)

        self.session.new_window(window_name='testing 3')
        self.assertEqual(2, int(self.session.attached_window().get('window_index')))

        logging.info(self.session.list_windows())
        print self.session.list_windows()
        try:
            self.session.select_window(1)
        except TmuxSessionNotFound:
            logging.info(self.session.list_windows())
            print self.session.list_windows()

        self.assertEqual(1, int(self.session.attached_window().get('window_index')))

        self.session.select_window('testing 3')
        self.assertEqual(2, int(self.session.attached_window().get('window_index')))

        self.assertEqual(len(self.session.list_windows()), 2)


class WindowNewTestCase(TmuxTestCase):

    def test_fresh_window_data(self):
        #self.session.select_window(1)
        current_windows = len(self.session._windows)
        self.session.attached_window().select_pane(1)
        self.session.attached_pane().send_keys('cd /srv/www/flaskr')
        self.session.attached_window().select_pane(0)
        self.session.attached_pane().send_keys('source .env/bin/activate')
        self.session.new_window(window_name='second')
        current_windows += 1
        self.assertEqual(current_windows, len(self.session._windows))
        self.session.new_window(window_name=3)
        current_windows += 1
        self.assertEqual(current_windows, len(self.session._windows))

        logging.info(self.session.list_windows())
        print self.session.list_windows()
        try:
            self.session.select_window(1)
        except TmuxSessionNotFound:
            logging.info(self.session.list_windows())
            print self.session.list_windows()



        self.session.kill_window(target_window=3)
        current_windows -= 1
        self.assertEqual(current_windows, len(self.session._windows))
        #tmux('display-panes')

    def test_newest_pane_data(self):
        self.session.attached_window()
        #self.session.select_window(1)

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
        self.assertIsInstance(pane, Pane)
        self.assertEqual(2, len(window._panes))

    def test_window_rename(self):
        window_name_before = 'test split window'
        window_name_after = 'testingdis_winname'
        window = self.session.new_window(window_name=window_name_before)
        self.assertEqual(window.get('window_name'), window_name_before)
        window = window.rename_window(window_name_after)
        self.assertEqual(window.get('window_name'), window_name_after)

    def test_new_window_automatic_rename(self):
        '''@todo'''
        pass

    def test_new_window_start_directory(self):
        '''@todo'''
        pass


if __name__ == '__main__':
    unittest.main()
