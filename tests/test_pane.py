# -*- coding: utf-8 -*-
"""Test for tmuxp Pane object."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging

logger = logging.getLogger(__name__)


def test_resize_pane(session):
    """ Test Pane.resize_pane(). """

    window = session.attached_window()
    window.rename_window('test_resize_pane')

    pane1 = window.attached_pane()
    pane1_height = pane1['pane_height']
    window.split_window()

    pane1.resize_pane(height=4)
    assert pane1['pane_height'] != pane1_height
    assert int(pane1['pane_height']) == 4

    pane1.resize_pane(height=3)
    assert int(pane1['pane_height']) == 3


def test_set_height(session):
    window = session.new_window(window_name='test_set_height')
    window.split_window()
    pane1 = window.attached_pane()
    pane1_height = pane1['pane_height']

    pane1.set_height(2)
    assert pane1['pane_height'] != pane1_height
    assert int(pane1['pane_height']) == 2


def test_set_width(session):
    window = session.new_window(window_name='test_set_width')
    window.split_window()

    window.select_layout('main-vertical')
    pane1 = window.attached_pane()
    pane1_width = pane1['pane_width']

    pane1.set_width(10)
    assert pane1['pane_width'] != pane1_width
    assert int(pane1['pane_width']) == 10

    pane1.reset()
