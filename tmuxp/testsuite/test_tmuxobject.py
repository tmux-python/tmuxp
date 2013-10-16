# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import unittest
from .. import Pane, Window
from .helpers import TmuxTestCase

from .. import log
import logging

logger = logging.getLogger(__name__)


class TmuxObjectTest(TmuxTestCase):
    ''' test the :class:`TmuxObject` base class object.
    '''

    def test_findWhere(self):
        '''findWhere'''

        window = self.session.attached_window()

        panes = window.list_panes()

        for pane in panes:
            pane_id = pane.get('pane_id')

            self.assertEqual(window.findWhere({'pane_id': pane_id}), pane)
            self.assertIsInstance(window.findWhere({'pane_id': pane_id}), Pane)

    def test_findWhere_multiple_attrs(self):
        '''.findWhere returns objects with multiple attributes
        '''

        window = self.session.attached_window()

        panes = window.list_panes()

        for pane in panes:
            pane_id = pane.get('pane_id')
            pane_index = pane.get('pane_index')

            self.assertEqual(window.findWhere({
                'pane_id': pane_id,
                'pane_index': pane_index
            }), pane)

    def test_where(self):
        '''.where'''

        window = self.session.attached_window()

        window.split_window()  # create second pane

        panes = window.list_panes()

        for pane in panes:
            pane_id = pane.get('pane_id')

            self.assertEqual(len(window.where({'pane_id': pane_id})), 1)
            self.assertIsInstance(window.where({'pane_id': pane_id}), list)
            self.assertEqual(window.where({'pane_id': pane_id})[0], pane)
            self.assertIsInstance(window.where({'pane_id': pane_id})[0], Pane)

    def test_getById(self):
        '''.getById'''

        window = self.session.attached_window()

        window.split_window()  # create second pane

        panes = window.list_panes()

        for pane in panes:
            pane_id = pane.get('pane_id')

            self.assertEqual(window.getById(pane_id), pane)
            self.assertIsInstance(window.getById(pane_id), Pane)

            self.assertIsNone(window.getById(324324321))


if __name__ == '__main__':
    unittest.main()
