# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import os
import unittest
from . import t
from .. import Window
from ..config import expand_config
from ..builder import Builder

from .helpers import TmuxTestCase
from .test_config import sampleconfigdict
import logging
logger = logging.getLogger(__name__)

TMUXWRAPPER_DIR = os.path.join(os.path.dirname(__file__), '.tmuxp')


class BuilderTest(TmuxTestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TMUXWRAPPER_DIR):
            os.makedirs(
                TMUXWRAPPER_DIR)
        super(BuilderTest, cls).setUpClass()

    def test_split_windows(self):
        s = self.session
        tmux_config = sampleconfigdict
        tmux_config = expand_config(tmux_config)
        logger.debug(tmux_config)

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
                self.assertEqual(window_pane_count, 1)
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


class BuilderTestN(BuilderTest):

    def _iter_create_windows(self, s, windows):
        ''' this is a generator that will create the windows and return the
        :class:`Window` object for the window.

        It handles the magic of cases where the user may want to start
        a session inside tmux (when `$TMUX` is in the env variables).

        :param: session: :class:`Session` from the config
        :param: windows: :py:obj:`list` of windows from the config
        '''

        for i, wconf in enumerate(windows, start=1):
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
                yield w
            else:
                w = s.new_window(window_name=window_name,
                                    automatic_rename=automatic_rename)
                yield w

    def test_split_windows(self):
        s = self.session
        tmux_config = sampleconfigdict
        tmux_config = expand_config(tmux_config)
        logger.debug(tmux_config)

        if 'session_name' in tmux_config:
            for w in self._iter_create_windows(s, tmux_config['windows']):
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
                    self.assertEqual(window_pane_count, 1)
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

class TestsToDo(object):
    def test_uses_first_window_if_exists(self):
        '''
        if the session is already on the first window, use that.

        this is useful if the user is already inside of a tmux session
        '''

    def test_same_session_already_exists_unclean(self):
        '''
        raise exception if session_name already exists and has multiple
        windows the user could potentially be offered to add a cli argument to
        override the session_name in config. Perhaps `-n` could be used to load
        a config from file with overridden session_name.
        '''

    def test_inside_tmux_same_session_already_exists(self):
        ''' same as above, but when the config file and the current $TMUX
        session are the same '''

    def test_inside_tmux_no_session_name_exists(self):
        '''
        if the session_name doesn't currently exist and the user is in tmux
        rename the current session by the config / -n and build there.
        '''

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
    #t.socket_name = 'tmuxp_test'
    unittest.main()
