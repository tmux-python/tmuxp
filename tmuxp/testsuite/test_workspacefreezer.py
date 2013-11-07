# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import os
import sys
import logging
import time
import kaptan
from .. import Window, config, exc
from ..workspacebuilder import WorkspaceBuilder, freeze
from .helpers import TmuxTestCase

logger = logging.getLogger(__name__)

current_dir = os.path.abspath(os.path.dirname(__file__))
example_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))


class FreezeTest(TmuxTestCase):

    yaml_config = """
    session_name: sampleconfig
    start_directory: '~'
    windows:
    - layout: main-vertical
      panes:
      - shell_command:
        - vim
        start_directory: '~'
      - shell_command:
        - echo "hey"
        - cd ../
      window_name: editor
    - panes:
      - shell_command:
        - tail -F /var/log/syslog
        start_directory: /var/log
      window_name: logging
    - window_name: test
      panes:
      - shell_command:
        - htop
    """

    def test_focus(self):
        # assure the built yaml config has focus
        pass

    def test_freeze_config(self):
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)
        builder.build(session=self.session)
        assert(self.session == builder.session)

        import time
        time.sleep(1)

        session = self.session
        sconf = freeze(session)

        config.validate_schema(sconf)

        sconf = config.inline(sconf)

        kaptanconf = kaptan.Kaptan()
        kaptanconf = kaptanconf.import_config(sconf)
        json = kaptanconf.export(
            'json',
            indent=2
        )
        yaml = kaptanconf.export(
            'yaml',
            indent=2,
            default_flow_style=False,
            safe=True
        )

        #logger.error(json)
        #logger.error(yaml)
