#!/usr/bin/env python

def interact(line, stdin, process):
#    print line
    pass


import unittest
import sys
import os
import subprocess
from tmuxp import t
import tmuxp.testsuite
from tmuxp.util import tmux

tmux_path = sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if tmux_path not in sys.path:
    sys.path.insert(0, tmux_path)


import os
import gevent
import gevent.subprocess
from gevent.subprocess import PIPE
import pexpect




#print shell(['tmux'], '')
#tmux('set-option', '-g', 'detach-on-destroy', 'off')
from time import sleep

def main():
    subprocess.Popen(['tmux'])
    sleep(1)
    suites = unittest.TestLoader().discover('tmuxp.testsuite', pattern="*.py")
    unittest.TextTestRunner(verbosity=2).run(suites)
    #tmuxprocess.kill()


if __name__ == '__main__':
    #p = gevent.subprocess.Popen(['tmux'], shell=True)
    #g = gevent.spawn(main)
    #out, err = p.communicate()
    #g.kill()
    main()
