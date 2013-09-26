import os
import shutil
import kaptan
import unittest
from .. import Window
from ..logxtreme import logging
from ..config import expand_config
from ..builder import Builder
from .helpers import TmuxTestCase
from .test_config import sampleconfigdict

TMUXWRAPPER_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')


class BuilderTestCase(TmuxTestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TMUXWRAPPER_DIR):
            os.makedirs(
                TMUXWRAPPER_DIR)
        super(BuilderTestCase, cls).setUpClass()

    def test_split_windows(self):
        s = self.session
        tmux_config = expand_config(sampleconfigdict)

        if 'session_name' in tmux_config:
            window_count = len(self.session._windows)  # current window count
            self.assertEqual(len(s.list_windows()), window_count)
            for i, wconf in enumerate(tmux_config['windows'], start=1):
                automatic_rename = False
                if 'window_name' not in wconf:
                    window_name = None
                    automatic_rename = True
                else:
                    window_name = wconf['window_name']

                if i == int(1):  # if first window, use window 1
                    #w = s.select_window(1)
                    w = s.attached_window()
                    w = w.rename_window(window_name)
                    w.list_panes()
                else:
                    w = s.new_window(window_name=window_name,
                                     automatic_rename=automatic_rename)
                    window_count += 1

                # current pane count, of course 1 since we just made it
                window_pane_count = len(w._panes)
                for pindex, pconf in enumerate(wconf['panes'], start=1):
                    if pindex != int(1):
                        p = w.split_window()
                        window_pane_count += 1
                    else:
                        p = w.attached_pane()
                    for cmd in pconf['shell_command']:
                        p.send_keys(cmd)
                    w.list_panes()
                    self.assertEqual(window_pane_count, len(w._panes))
                self.assertIsInstance(w, Window)
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
