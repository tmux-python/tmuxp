import os
import shutil
import kaptan
import unittest
from sh import tmux, ErrorReturnCode_1
from . import TestTmux


TMUXWRAPPER_DIR = os.path.join(os.path.dirname(__file__), '.tmuxwrapper')


class BuilderTest(TestTmux):

    @classmethod
    def setUpClass(cls):
        # run parent
        # setUpClass
        if not os.path.exists(TMUXWRAPPER_DIR):
            os.makedirs(
                TMUXWRAPPER_DIR)
        super(BuilderTest, cls).setUpClass()

    def testPaneProportions(self):
        """
        todo. checking the proportions of a pane on a grid allows
        us to verify a window has been build correctly without
        needing to see the tmux session itself.

        we expect panes in a list to be ordered and show up to
        their corresponding pane_index.
        """
        pass
