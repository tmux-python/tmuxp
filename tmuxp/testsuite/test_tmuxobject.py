# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import random
from .. import Pane, Window, Session
from . import t
from .helpers import TmuxTestCase

import logging

logger = logging.getLogger(__name__)


class TmuxObjectTest(TmuxTestCase):

    """Test the :class:`TmuxRelationalObject` base class object."""

    def test_findWhere(self):
        """findWhere."""
        self.maxDiff = None
        # server.findWhere
        for session in t.sessions:
            session_id = session.get('session_id')

            self.assertEqual(t.findWhere({'session_id': session_id}), session)
            self.assertIsInstance(t.findWhere({
                                  'session_id': session_id}), Session)

            # session.findWhere
            for window in session.windows:
                window_id = window.get('window_id')

                self.assertEqual(
                    session.findWhere({'window_id': window_id}), window
                )
                self.assertIsInstance(
                    session.findWhere({'window_id': window_id}), Window
                )

                # window.findWhere
                for pane in window.panes:
                    pane_id = pane.get('pane_id')

                    self.assertEqual(window.findWhere(
                        {'pane_id': pane_id}), pane)
                    self.assertIsInstance(window.findWhere(
                        {'pane_id': pane_id}), Pane)

    def test_findWhere_multiple_attrs(self):
        """.findWhere returns objects with multiple attributes."""

        for session in t.sessions:
            session_id = session.get('session_id')
            session_name = session.get('session_name')
            find_where = t.findWhere({
                'session_id': session_id,
                'session_name': session_name
            })

            self.assertEqual(find_where, session)
            self.assertIsInstance(find_where, Session)

            # session.findWhere
            for window in session.windows:
                window_id = window.get('window_id')
                window_index = window.get('window_index')

                find_where = session.findWhere({
                    'window_id': window_id,
                    'window_index': window_index
                })

                self.assertEqual(find_where, window)
                self.assertIsInstance(find_where, Window)

                # window.findWhere
                for pane in window.panes:
                    pane_id = pane.get('pane_id')
                    pane_tty = pane.get('pane_tty')

                    find_where = window.findWhere({
                        'pane_id': pane_id,
                        'pane_tty': pane_tty
                    })

                    self.assertEqual(find_where, pane)
                    self.assertIsInstance(find_where, Pane)

    def test_where(self):
        """.where"""

        window = self.session.attached_window()
        window.split_window()  # create second pane

        for session in t.sessions:
            session_id = session.get('session_id')
            session_name = session.get('session_name')
            where = t.where({
                'session_id': session_id,
                'session_name': session_name
            })

            self.assertEqual(len(where), 1)
            self.assertIsInstance(where, list)
            self.assertEqual(where[0], session)
            self.assertIsInstance(where[0], Session)

            # session.where
            for window in session.windows:
                window_id = window.get('window_id')
                window_index = window.get('window_index')

                where = session.where({
                    'window_id': window_id,
                    'window_index': window_index
                })

                self.assertEqual(len(where), 1)
                self.assertIsInstance(where, list)
                self.assertEqual(where[0], window)
                self.assertIsInstance(where[0], Window)

                # window.where
                for pane in window.panes:
                    pane_id = pane.get('pane_id')
                    pane_tty = pane.get('pane_tty')

                    where = window.where({
                        'pane_id': pane_id,
                        'pane_tty': pane_tty
                    })

                    self.assertEqual(len(where), 1)
                    self.assertIsInstance(where, list)
                    self.assertEqual(where[0], pane)
                    self.assertIsInstance(where[0], Pane)

    def test_getById(self):
        """.getById"""

        window = self.session.attached_window()

        window.split_window()  # create second pane

        for session in t.sessions:
            session_id = session.get('session_id')
            session_name = session.get('session_name')
            get_by_id = t.getById(session_id)

            self.assertEqual(get_by_id, session)
            self.assertIsInstance(get_by_id, Session)
            self.assertIsNone(t.getById(
                '$' + str(random.randint(50000, 90000))
            ))

            # session.getById
            for window in session.windows:
                window_id = window.get('window_id')
                window_index = window.get('window_index')

                get_by_id = session.getById(window_id)

                self.assertEqual(get_by_id, window)
                self.assertIsInstance(get_by_id, Window)

                self.assertIsNone(session.getById(
                    '@' + str(random.randint(50000, 90000))
                ))

                # window.getById
                for pane in window.panes:
                    pane_id = pane.get('pane_id')
                    pane_tty = pane.get('pane_tty')

                    get_by_id = window.getById(pane_id)

                    self.assertEqual(get_by_id, pane)
                    self.assertIsInstance(get_by_id, Pane)
                    self.assertIsNone(window.getById(
                        '%' + str(random.randint(50000, 90000))
                    ))
