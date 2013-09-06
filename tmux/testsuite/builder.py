import os
import shutil
import kaptan
import unittest
from sh import tmux, ErrorReturnCode_1
from .helpers import TestTmux
from .config import sampleconfigdict
from tmux import Window


TMUXWRAPPER_DIR = os.path.join(os.path.dirname(__file__), '.tmuxwrapper')


def build_windows(window):
    '''
    builds the window object.

    window
        :class:`Window` object.
    '''
    pass


class BuilderTest(TestTmux):

    @classmethod
    def setUpClass(cls):
        # run parent
        # setUpClass
        if not os.path.exists(TMUXWRAPPER_DIR):
            os.makedirs(
                TMUXWRAPPER_DIR)
        super(BuilderTest, cls).setUpClass()

    def test_split_windows(self):
        session_name = self.TEST_SESSION_NAME
        s = self.session
        tmux_config = sampleconfigdict

        if 'session_name' in tmux_config:
            window_count = len(self.session._windows)  # current window count
            self.assertEqual(len(s.list_windows()), window_count)
            for w in tmux_config['windows']:
                if 'window_name' not in w:
                    window_name = None
                else:
                    window_name = w['window_name']

                winObject = s.new_window(window_name=window_name)
                # current pane count, of course 1 since we just made it
                window_pane_count = len(winObject._panes)
                for pane in w['panes']:
                    winObject.split_window()
                    window_pane_count += 1
                    self.assertEqual(window_pane_count, len(winObject._panes))
                self.assertIsInstance(winObject, Window)
                window_count += 1
                self.assertEqual(len(s.list_windows()), window_count)

        else:
            raise ValueError('config requires session_name')

    def testPaneProportions(self):
        """
        todo. checking the proportions of a pane on a grid allows
        us to verify a window has been build correctly without
        needing to see the tmux session itself.

        we expect panes in a list to be ordered and show up to
        their corresponding pane_index.
        """
        pass


if __name__ == '__main__':
    unittest.main()
