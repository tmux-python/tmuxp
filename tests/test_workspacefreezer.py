# -*- coding: utf-8 -*-
"""Test for tmuxp workspacefreezer."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import time

import kaptan

from tmuxp import config
from tmuxp.workspacebuilder import WorkspaceBuilder, freeze

from .helpers import TmuxTestCase
from .fixtures._util import loadfixture

logger = logging.getLogger(__name__)


class FreezeTest(TmuxTestCase):

    yaml_config = loadfixture("workspacefreezer/sampleconfig.yaml")

    def test_focus(self):
        # assure the built yaml config has focus
        pass

    def test_freeze_config(self):
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)
        builder.build(session=self.session)
        assert self.session == builder.session

        time.sleep(.50)

        session = self.session
        sconf = freeze(session)

        config.validate_schema(sconf)

        sconf = config.inline(sconf)

        kaptanconf = kaptan.Kaptan()
        kaptanconf = kaptanconf.import_config(sconf)
        kaptanconf.export(
            'json',
            indent=2
        )
        kaptanconf.export(
            'yaml',
            indent=2,
            default_flow_style=False,
            safe=True
        )
