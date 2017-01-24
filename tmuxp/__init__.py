# -*- coding: utf-8 -*-
# flake8: NOQA
"""tmux session manager.

tmuxp
~~~~~

:copyright: Copyright 2013-2017 Tony Narlock.
:license: BSD, see LICENSE for details

"""
from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

from .__about__ import __title__, __package_name__, __version__, \
    __description__, __email__, __author__, __license__, __copyright__

from .workspacebuilder import WorkspaceBuilder

from . import config, util, cli
