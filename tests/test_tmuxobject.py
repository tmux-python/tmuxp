# -*- coding: utf-8 -*-
"""Test for tmuxp TmuxRelationalObject and TmuxMappingObject."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging

from tmuxp import Pane, Session, Window
from .helpers import TEST_SESSION_PREFIX, TmuxTestCase, namer

logger = logging.getLogger(__name__)


class TmuxObjectTest(TmuxTestCase):

    """Test the :class:`TmuxRelationalObject` base class object."""

    def test_findWhere(self):
        """Test that findWhere() retrieves single matching object."""
        self.maxDiff = None
        # server.findWhere
        for session in self.t.sessions:
            session_id = session.get('session_id')

            assert self.t.findWhere({'session_id': session_id}) == session
            assert isinstance(self.t.findWhere({
                'session_id': session_id
            }), Session)

            # session.findWhere
            for window in session.windows:
                window_id = window.get('window_id')

                assert session.findWhere({'window_id': window_id}) == window
                assert isinstance(
                    session.findWhere({'window_id': window_id}), Window
                )

                # window.findWhere
                for pane in window.panes:
                    pane_id = pane.get('pane_id')

                    assert window.findWhere({'pane_id': pane_id}) == pane
                    assert isinstance(
                        window.findWhere({'pane_id': pane_id}), Pane)

    def test_findWhere_None(self):
        """.findWhere returns None if no results found."""

        while True:
            nonexistant_session = TEST_SESSION_PREFIX + next(namer)

            if not self.t.has_session(nonexistant_session):
                break

        assert self.t.findWhere({
            'session_name': nonexistant_session
        }) is None

    def test_findWhere_multiple_attrs(self):
        """.findWhere returns objects with multiple attributes."""

        for session in self.t.sessions:
            session_id = session.get('session_id')
            session_name = session.get('session_name')
            find_where = self.t.findWhere({
                'session_id': session_id,
                'session_name': session_name
            })

            assert find_where == session
            assert isinstance(find_where, Session)

            # session.findWhere
            for window in session.windows:
                window_id = window.get('window_id')
                window_index = window.get('window_index')

                find_where = session.findWhere({
                    'window_id': window_id,
                    'window_index': window_index
                })

                assert find_where == window
                assert isinstance(find_where, Window)

                # window.findWhere
                for pane in window.panes:
                    pane_id = pane.get('pane_id')
                    pane_tty = pane.get('pane_tty')

                    find_where = window.findWhere({
                        'pane_id': pane_id,
                        'pane_tty': pane_tty
                    })

                    assert find_where == pane
                    assert isinstance(find_where, Pane)

    def test_where(self):
        """Test self.where() returns matching objects."""

        window = self.session.attached_window()
        window.split_window()  # create second pane

        for session in self.t.sessions:
            session_id = session.get('session_id')
            session_name = session.get('session_name')
            where = self.t.where({
                'session_id': session_id,
                'session_name': session_name
            })

            assert len(where) == 1
            assert isinstance(where, list)
            assert where[0] == session
            assert isinstance(where[0], Session)

            # session.where
            for window in session.windows:
                window_id = window.get('window_id')
                window_index = window.get('window_index')

                where = session.where({
                    'window_id': window_id,
                    'window_index': window_index
                })

                assert len(where) == 1
                assert isinstance(where, list)
                assert where[0] == window
                assert isinstance(where[0], Window)

                # window.where
                for pane in window.panes:
                    pane_id = pane.get('pane_id')
                    pane_tty = pane.get('pane_tty')

                    where = window.where({
                        'pane_id': pane_id,
                        'pane_tty': pane_tty
                    })

                    assert len(where) == 1
                    assert isinstance(where, list)
                    assert where[0] == pane
                    assert isinstance(where[0], Pane)

    def test_getById(self):
        """Test self.getById() retrieves child object."""

        window = self.session.attached_window()

        window.split_window()  # create second pane

        for session in self.t.sessions:
            session_id = session.get('session_id')
            get_by_id = self.t.getById(session_id)

            assert get_by_id == session
            assert isinstance(get_by_id, Session)
            assert self.t.getById('$' + next(namer)) is None

            # session.getById
            for window in session.windows:
                window_id = window.get('window_id')

                get_by_id = session.getById(window_id)

                assert get_by_id == window
                assert isinstance(get_by_id, Window)

                assert session.getById('@' + next(namer)) is None

                # window.getById
                for pane in window.panes:
                    pane_id = pane.get('pane_id')

                    get_by_id = window.getById(pane_id)

                    assert get_by_id == pane
                    assert isinstance(get_by_id, Pane)
                    assert window.getById('%' + next(namer)) is None
