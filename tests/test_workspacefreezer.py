# -*- coding: utf-8 -*-
"""Test for tmuxp workspacefreezer."""

from __future__ import absolute_import, unicode_literals

import time

import kaptan

from tmuxp import config
from tmuxp.workspacebuilder import WorkspaceBuilder, freeze

from .fixtures._util import loadfixture


def test_freeze_config(session):
    yaml_config = loadfixture("workspacefreezer/sampleconfig.yaml")
    sconfig = kaptan.Kaptan(handler='yaml')
    sconfig = sconfig.import_config(yaml_config).get()

    builder = WorkspaceBuilder(sconf=sconfig)
    builder.build(session=session)
    assert session == builder.session

    time.sleep(0.50)

    session = session
    sconf = freeze(session)

    config.validate_schema(sconf)

    sconf = config.inline(sconf)

    kaptanconf = kaptan.Kaptan()
    kaptanconf = kaptanconf.import_config(sconf)
    kaptanconf.export('json', indent=2)
    kaptanconf.export('yaml', indent=2, default_flow_style=False, safe=True)
