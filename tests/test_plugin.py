# -*- coding: utf-8 -*-
"""Test for tmuxp plugin api."""
from __future__ import absolute_import

import json
import os

import pytest

import libtmux
from libtmux.common import has_lt_version
from tmuxp.plugin import TmuxpPluginInterface
from tmuxp.exc import TmuxpPluginException

from .fixtures.pluginsystem.partials.all_pass import AllVersionPassPlugin
from .fixtures.pluginsystem.partials.tmux_version_fail import (
    TmuxVersionFailMinPlugin,
    TmuxVersionFailMaxPlugin,
    TmuxVersionFailIncompatiblePlugin
)
from .fixtures.pluginsystem.partials.tmuxp_version_fail import (
    TmuxpVersionFailMinPlugin,
    TmuxpVersionFailMaxPlugin,
    TmuxpVersionFailIncompatiblePlugin 
)


def test_all_pass():
    try:
        plugin = AllVersionPassPlugin()
        assert(True)
    except TmuxpPluginException as error:
        assert(False)


def test_tmux_version_fail_min():
    try:
        plugin = TmuxVersionFailMinPlugin()
        assert(False)
    except TmuxpPluginException as error:
        assert('Incompatible' in error.__str__())


def test_tmux_version_fail_max():
    try:
        plugin = TmuxVersionFailMaxPlugin()
        assert(False)
    except TmuxpPluginException as error:
        assert('Incompatible' in error.__str__())


def test_tmux_version_fail_incompatible():
    try:
        plugin = TmuxVersionFailIncompatiblePlugin()
        assert(False)
    except TmuxpPluginException as error:
        assert('Incompatible' in error.__str__())


def test_tmuxp_version_fail_min():
    try:
        plugin = TmuxpVersionFailMinPlugin()
        assert(False)
    except TmuxpPluginException as error:
        assert('Incompatible' in error.__str__())


def test_tmux_version_fail_max():
    try:
        plugin = TmuxpVersionFailMaxPlugin()
        assert(False)
    except TmuxpPluginException as error:
        assert('Incompatible' in error.__str__())


def test_tmux_version_fail_incompatible():
    try:
        plugin = TmuxpVersionFailIncompatiblePlugin()
        assert(False)
    except TmuxpPluginException as error:
        assert('Incompatible' in error.__str__())