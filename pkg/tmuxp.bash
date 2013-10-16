#!/usr/bin/env python
# -*- coding: utf8 - *-

import os
from tmuxp import cli

if __name__ == '__main__':

    cline = os.environ.get('COMP_LINE') or os.environ.get('COMMAND_LINE') or ''
    cpoint = int(os.environ.get('COMP_POINT') or len(cline))

    cli.complete(cline, cpoint)
