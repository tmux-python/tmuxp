# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import os
import unittest
import logging
import time
import kaptan
from .. import Window, config, exc
from ..workspacebuilder import WorkspaceBuilder
from .helpers import TmuxTestCase

logger = logging.getLogger(__name__)

current_dir = os.path.abspath(os.path.dirname(__file__))
example_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))


def freeza(session):
    sconf = {}

    sconf['session_name'] = session['session_name']

    sconf['windows'] = []
    for w in session.windows:
        wconf = {}
        wconf['options'] = w.show_window_options()
        wconf['window_name'] = w.get('window_name')
        wconf['panes'] = []
        logger.error(w)
        logger.error(dict(w))

        for p in w.panes:
            pconf = {}
            pconf['shell_command'] = []
            pconf['shell_command'].append('cd ' + p.get('pane_current_path'))
            pconf['shell_command'].append(p.get('pane_current_command'))
            wconf['panes'].append(pconf)
            logger.error(p)
            logger.error(dict(p))


        sconf['windows'].append(wconf)

    logger.error(sconf)

    return sconf






class FreezeTest(TmuxTestCase):

    yaml_config = '''
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
    '''

    def test_split_windows(self):
        sconfig = kaptan.Kaptan(handler='yaml')
        sconfig = sconfig.import_config(self.yaml_config).get()

        builder = WorkspaceBuilder(sconf=sconfig)
        builder.build(session=self.session)
        assert(self.session == builder.session)

        import time
        time.sleep(1)

        session = self.session
        sconf = freeza(session)

        config.check_consistency(sconf)

        sconf = config.inline(sconf)

        kaptanconf = kaptan.Kaptan()
        kaptanconf = kaptanconf.import_config(sconf)
        json = kaptanconf.export('json', indent=2)
        json = kaptanconf.export('json', indent=2)
        yaml = kaptanconf.export(
            'yaml', indent=2, default_flow_style=False, safe=True)


        logger.error(json)
        logger.error(yaml)

if __name__ == '__main__':
    unittest.main()
