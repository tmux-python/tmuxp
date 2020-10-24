# -*- coding: utf-8 -*-
"""Test for tmuxp plugin api."""
from __future__ import absolute_import

from tmuxp.exc import TmuxpPluginException

from .fixtures.pluginsystem.partials.all_pass import AllVersionPassPlugin
from .fixtures.pluginsystem.partials.tmux_version_fail import (
    TmuxVersionFailMinPlugin,
    TmuxVersionFailMaxPlugin,
    TmuxVersionFailIncompatiblePlugin,
)
from .fixtures.pluginsystem.partials.libtmux_version_fail import (
    LibtmuxVersionFailMinPlugin,
    LibtmuxVersionFailMaxPlugin,
    LibtmuxVersionFailIncompatiblePlugin,
)
from .fixtures.pluginsystem.partials.tmuxp_version_fail import (
    TmuxpVersionFailMinPlugin,
    TmuxpVersionFailMaxPlugin,
    TmuxpVersionFailIncompatiblePlugin,
)


def test_all_pass():
    try:
        AllVersionPassPlugin()
        assert True
    except TmuxpPluginException:
        assert False


def test_tmux_version_fail_min():
    try:
        TmuxVersionFailMinPlugin()
        assert False
    except TmuxpPluginException as error:
        assert 'Incompatible' in error.__str__()


def test_tmux_version_fail_max():
    try:
        TmuxVersionFailMaxPlugin()
        assert False
    except TmuxpPluginException as error:
        assert 'Incompatible' in error.__str__()


def test_tmux_version_fail_incompatible():
    try:
        TmuxVersionFailIncompatiblePlugin()
        assert False
    except TmuxpPluginException as error:
        assert 'Incompatible' in error.__str__()


def test_tmuxp_version_fail_min():
    try:
        TmuxpVersionFailMinPlugin()
        assert False
    except TmuxpPluginException as error:
        assert 'Incompatible' in error.__str__()


def test_tmuxp_version_fail_max():
    try:
        TmuxpVersionFailMaxPlugin()
        assert False
    except TmuxpPluginException as error:
        assert 'Incompatible' in error.__str__()


def test_tmuxp_version_fail_incompatible():
    try:
        TmuxpVersionFailIncompatiblePlugin()
        assert False
    except TmuxpPluginException as error:
        assert 'Incompatible' in error.__str__()


def test_libtmux_version_fail_min():
    try:
        LibtmuxVersionFailMinPlugin()
        assert False
    except TmuxpPluginException as error:
        assert 'Incompatible' in error.__str__()


def test_libtmux_version_fail_max():
    try:
        LibtmuxVersionFailMaxPlugin()
        assert False
    except TmuxpPluginException as error:
        assert 'Incompatible' in error.__str__()


def test_libtmux_version_fail_incompatible():
    try:
        LibtmuxVersionFailIncompatiblePlugin()
        assert False
    except TmuxpPluginException as error:
        assert 'Incompatible' in error.__str__()
