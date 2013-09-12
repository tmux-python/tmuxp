"""
    tmuxwrapper
    ~~~~~~~~~~~

    tmuxwrapper helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock <tony@git-pull.com>.
    :license: BSD, see LICENSE for details

    Terminology I use in documentation:

    ``tmux(1)``
        the actual tmux application, a la unix manpages, see
        http://superuser.com/a/297705.

    ``MetaData`` or the ``_TMUX`` attribute in objects
        information ``tmux(1)`` returns on certain commands listing or creating
        sessions, windows nad panes.

    server

        ``man tmux(1)``::

            The tmux server manages clients, sessions, windows and panes.

    session
        used by ``tmux(1)`` to hold windows, panes. its' counterpart is
        :class:`Session` object.

        ``man tmux(1)``::

            Clients are attached to sessions to interact with them, either when
            they are created with the new-session command, or later with the
            attach-session command. Each session has one of more windows linked
            into it.

        Identifier:
            ``session id``, i.e. $390

    window
        used by ``tmux(1)``. holds panes. new window only has one pane.
        ``tmux(1)``'s ``split-window`` can create panes horizontally or
        vertically. represented by :class:`Window`

        ``man tmux(1)``::

            Windows may be linked to multiple sessions and are made up of one
            or more panes, each of which contains a pseudo terminal.

        Identifier:
            ``window_id``,  i.e.  @566

    pane
        an individual pseudo terminal / shell prompt. represented by the
        :class:`Pane` object.

        Identifier:
            ``pane_id``, i.e. %1334

    :meth:`from_tmux`
        pulls information from a live tmux server.

    target and -t
        from ``tmux(1)``.

    Magic
        the ``MetaData`` in ``_TMUX`` attributes on :class:`Session`,
        :class:`Window` and :class:`Pane` objects is used to pull a reference
        from a global object. :attrib:`_session` and :attrib:`_window`
        in ``Window`` and ``Pane`` are properties that forward to that.

    Which tmux client is used?
        tmux allows for multiple clients and sessions. ``tmuxwrapper`` will
        interact with the most recently attached client you attached. When
        testing, just run a ``tmux`` in shell and do what you have to do.

    fnmatch
        tmuxwrapper is intended to work with fnmatch compatible functions. If
        an fnmatch isn't working at the API level, please file an issue.

    Limitations
        You may only have one client attached to use certain functions

        Defaults to current client for ``target-client``
        :meth:`Server.attached_session()` can return anything that's attached

        References to _windows and _panes are weak and easily flushed. In the
        future versions we will be able to hold onto _windows and _panes by
        unique identifier window_id/pane_id and if a window or pane is closed,
        we can give call the pane or window a phantom / dead.

        The above will bring tmuxwrapper closer to being able to handle a tmux
        server by objects over where a client may be interacted with while
        Session, Window and Pane objects are active.

"""
import os
import sys
import kaptan
from pprint import pprint
from tmuxp.util import tmux
from tmuxp.formats import SESSION_FORMATS, WINDOW_FORMATS, PANE_FORMATS
#LOG_FORMAT = "(%(levelname)s) %(filename)s:%(lineno)s.%(funcName)s : %(asctime)-15s:\n\t%(message)s"
#logging.basicConfig(format=LOG_FORMAT, level='DEBUG')


#for session in Server.list_sessions():
#    for window in session.windows:
#        for pane in window.panes:
#            pass


TMUXWRAPPER_DIR = os.path.expanduser('~/.tmuxwrapper')

if os.path.exists(TMUXWRAPPER_DIR):
    for r, d, f in os.walk(TMUXWRAPPER_DIR):
        for filela in (x for x in f if x.endswith(('.json', '.ini', 'yaml'))):
            thefile = os.path.join(TMUXWRAPPER_DIR, filela)
            print('filename: %s\t \tfullfile: %s\t' % (filela, thefile))
            c = kaptan.Kaptan()
            c.import_config(thefile)

            #pprint(c.get("windows"))
            #pprint(c.export('dict'))
            pprint(c.get())

#config = kaptan.Kaptan(handler="yaml")
#config.import_config("""
#    name: hi
#    windows:
#        - editor:
#            layout: main-vertical
#            panes:
#                - vim
#                - cowsay "hey"
#        - server: htop
#        - logs: tail -f logs/development.log
#    """)

#print(config.get('windows'))
""" expand inline config
    dict({'session_name': { dict })

    to

    dict({ name='session_name', **dict})
"""
windows = list()
for window in c.get('windows'):

    if len(window) == int(1):
        name = window.iterkeys().next()  # get window name

        """expand
            window[name] = 'command'

            to

            window[name] = {
                panes=['command']
            }
        """
        if isinstance(window[name], basestring):
            windowoptions = dict(
                panes=[window[name]]
            )
        else:
            windowoptions = window[name]

        window = dict(name=name, **windowoptions)
        if len(window['panes']) > int(1):
            pass

    windows.append(window)

import os
import gevent
import gevent.subprocess
import subprocess
from gevent.subprocess import PIPE
import pexpect



def shell(args, input):
    #p = pexpect.spawn('tmux')
    #p.interact()
    p = gevent.subprocess.call(args, shell=True)

#print shell(['vim'], '')



def has_virtualenv():
    if os.environ.get('VIRTUAL_ENV'):
        return os.environ.get('VIRTUAL_ENV')
    else:
        False

def in_tmux():
    if os.environ.get('TMUX'):
        return True
    else:
        return False

print has_virtualenv()
print in_tmux()

import itertools
#subprocess.Popen(['vim']).pid
if not in_tmux():
    shell_commands = []
    if has_virtualenv():
        shell_commands.append('source %s/bin/activate' % has_virtualenv())

    shell_commands.append('echo wat lol %s' % has_virtualenv())
    #shell_commands = ['send-keys ' + shell_command + '\;' for shell_command in shell_commands]
    #shell_commands.append('attach')
    #sep = ['\;'] * (len(shell_commands) - 1)
    #shell_commands = list(it.next() for it in itertools.cycle((iter(shell_commands), iter(sep))))
    print shell_commands
    #os.execl('/usr/local/bin/tmux', 'new-session -d', *shell_commands)
    session_name = 'tmuxp'
    subprocess.call(['/usr/local/bin/tmux', 'new-session', '-d', '-s %s' % session_name])
    for shell_command in shell_commands:
        subprocess.call(['/usr/local/bin/tmux', 'send-keys', '-t %s' % session_name, shell_command, '^M'])

    subprocess.call(['/usr/local/bin/tmux', 'send-keys', '-R', '-t %s' % session_name, 'python main.py', '^M'])

    os.execl('/usr/local/bin/tmux', 'tmux', 'attach-session', '-t %s'% session_name)
else:
    print "welcome to tmuxp"

exit()

"""
Have a bootstrap.py to determine environment variables, like tmux location,
if inside tmux, is tmux server running, current config files, current
sessions. An outer wrapper that can be used to run tmux within created,
uncreated and remotely.
"""
