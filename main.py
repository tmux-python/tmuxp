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
import kaptan
from sh import tmux, cut, ErrorReturnCode_1
from pprint import pprint
from formats import SESSION_FORMATS, WINDOW_FORMATS, PANE_FORMATS
import sys
import os
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
            print("%s %s" % (filela, type(filela)))
            thefile = os.path.join(TMUXWRAPPER_DIR, filela)
            print("%s" % thefile)
            print("%s" % type(thefile))
            c = kaptan.Kaptan()
            c.import_config(thefile)

            pprint(c.get("windows"))

config = kaptan.Kaptan(handler="yaml")
config.import_config("""
    name: hi
    windows:
        - editor:
            layout: main-vertical
            panes:
                - vim
                - cowsay "hey"
        - server: htop
        - logs: tail -f logs/development.log
    """)

print(config.get('windows'))
""" expand inline config
    dict({'session_name': { dict })

    to

    dict({ name='session_name', **dict})
"""
windows = list()
for window in config.get('windows'):

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
