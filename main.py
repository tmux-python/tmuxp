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
        used by ``tmux(1). holds panes. new window only has one pane.
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
from functools import wraps
import logging
import sys
from logxtreme import RainbowLoggingHandler
#LOG_FORMAT = "(%(levelname)s) %(filename)s:%(lineno)s.%(funcName)s : %(asctime)-15s:\n\t%(message)s"
#logging.basicConfig(format=LOG_FORMAT, level='DEBUG')

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

handler = RainbowLoggingHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
root_logger.addHandler(handler)
logger = logging.getLogger("test")


def tmuxa(*args, **kwargs):
    '''
    wrap tmux from ``sh`` library in a try catch
    '''
    try:
        #return tmx(*args, **kwargs)
        pass
    except ErrorReturnCode_1 as e:

        if e.stderr.startswith('session not found'):
            raise SessionNotFound('session not found')

        logging.error(
            "\n\tcmd:\t%s\n"
            "\terror:\t%s"
            % (e.full_cmd, e.stderr)
        )
        return e.stderr


class SessionNotFound(Exception):
    pass


def live_tmux(f):
    '''
    decorator that checks for :attrib:`_TMUX` inside :class:`Session`,
    :class:`Window` and :class:`Pane` objects.

    :attrib:`_TMUX` stores valuable information for an tmux object's life
    cycle. Hereinafter, I will call this ``MetaData``

    ``tmux( returns information

    @todo: in the future, :class:`Pane` will have ``PANE_FORMATS``,
    ``WINDOW_FORMATS`` and ``Session_FORMATS`` metadata, and :class:`Window`
    will have ``WINDOW_FORMATS`` and ``Session_FORMATS`` If a :attrib:`_TMUX
    exists, it should be possible to do a lookup for its parent :class:`Window`
    or :class:`Pane` object.

    Because this data is live in the system, caching strategy isn't a priority.

    If a session is imported directly from a configuration or is otherwise
    being built manually via CLI or scripting, :attrib:`_TMUX` is populated
    when:

    A tmux session is created with:

    :meth:`Session.create_session` aka ``tmux create-session``

    :meth:`Server.list_sessions` aka ``tmux list-sessions``
    :meth:`Session.new_window` aka ``tmux new-window``
    :meth:`Window.split_window` aka ``tmux split-window``
        returns a :class:`Pane` with pane metadata

        - its first :class:`Window`, in :attrib:`_windows`, and subsequently,
          and the :class:`Window`'s first :class:`Pane` in :attrib:`_panes`
          is populated with :attrib:`_TMUX` This is returned because the

            attributes.
        - a window is created with :meth:`Session.create_session`
    '''
    @wraps(f)
    def live_tmux(self, *args, **kwargs):
        if not self._TMUX:
            raise NotRunning(
                "self._TMUX not found, this object is not part of an active"
                "tmux session. If you need help please post an issue on github"
            )
        return f(self, *args, **kwargs)
    return live_tmux


class NoClientException(object):
    pass


class SessionExists(Exception):
    pass


class NotRunning(Exception):
    '''
        class for when ._TMUX doesn't exist, this will cause an issue with
        building the workspace and running commands
    '''
    pass


class Session(object):
    '''
    tmux session
    '''

    def __init__(self, **kwargs):

        self.session_name = None
        self._windows = list()

        # do we need this?
        if 'session_name' not in kwargs:
            raise ValueError('Session requires session_name')
        else:
            self.session_name = kwargs['session_name']

    @classmethod
    def new_session(cls,
                    session_name=None,
                    kill_session=False):
        '''
        ``tmux(1)`` ``new-session``

        Returns :class:`Session`

        Uses ``-P`` flag to print session info, ``-F`` for return formatting
        returns new Session object

        kill_session
            Kill current session if ``tmux has-session`` Useful for testing
            workspaces.
        '''
        try:
            # test this, returning NoneType
            if not len(tmux('has-session', '-t', session_name)):
                if kill_session:
                    tmux('kill-session', '-t', session_name)
                    logging.debug('session %s exists. killed it.' % session_name)
                else:
                    raise SessionExists('Session named %s exists' % session_name)
        except ErrorReturnCode_1:
            pass

        logging.debug('creating session %s' % session_name)

        formats = SESSION_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        session_info = tmux(
            'new-session',
            '-d',
            '-s', session_name,
            '-P', '-F%s' % '\t'.join(tmux_formats),   # output
        )

        # combine format keys with values returned from ``tmux list-windows``
        session_info = dict(zip(formats, session_info.split('\t')))

        # clear up empty dict
        session_info = dict((k, v) for k, v in session_info.iteritems() if v)

        session = cls(session_name=session_name)
        session._TMUX = dict()
        for (k, v) in session_info.items():
            session._TMUX[k] = v

        # need to be able to get first windows
        session._windows = session.list_windows()

        return session

    @live_tmux
    def new_window(self, window_name=None):
        '''
        tmux(1) new-window

        window_name
            string. window name (-n)
        '''

        if window_name:
            tmux(
                'new-window',
                '-t', self.session_name,
                '-n', window_name
            )
        else:
            tmux(
                'new-window',
                '-t', self.session_name
            )

        self.list_windows()

    @live_tmux
    def kill_window(self, *args, **kwargs):
        '''
        tmux(1) kill-window

        Kill the current window or the window at ``target-window``. removing it
        from any sessions to which it is linked. The ``-a`` option kills all
        but the window given to ``-t``.

        -a
            string arg.
        '''

        tmux_args = list()

        if '-a' in args:
            tmux_args.append('-a')

        if 'target_window' in kwargs:
            tmux_args.append(['-t', kwargs['target_window']])

        tmux('kill-window', *tmux_args)

        self.list_windows()

    @classmethod
    def from_tmux(cls, **kwargs):
        '''
        Freeze of the current tmux session directly from the server. Returns
        :class:`Session`

        session_name
            name of the tmux session

        '''
        if 'session_name' not in kwargs:
            raise ValueError('Session requires session_name')

        session = cls(session_name=kwargs['session_name'])
        session._TMUX = dict()
        for (k, v) in kwargs.items():
            session._TMUX[k] = v

        session._windows = session.list_windows()

        return session

    @live_tmux
    def _list_windows(self):
        '''
        Return dict of ``tmux(1) list-windows`` values.
        '''

        formats = ['session_name', 'session_id'] + WINDOW_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        windows = tmux(
            'list-windows',                     # ``tmux list-windows``
            '-t%s' % self.session_name,    # target (session name)
            '-F%s' % '\t'.join(tmux_formats),   # output
            _iter=True                          # iterate line by line
        )

        # combine format keys with values returned from ``tmux list-windows``
        windows = [dict(zip(formats, window.split('\t'))) for window in windows]

        # clear up empty dict
        windows = [
            dict((k, v) for k, v in window.iteritems() if v) for window in windows
        ]

        return windows

    @live_tmux
    def list_windows(self):
        '''
        Return a list of :class:`Window` from the ``tmux(1)`` session.
        '''

        #windows = [Window.from_tmux(session=self, **window) for window in self._list_windows()]
        new_windows = self._list_windows()

        if not self._windows:
            for window in new_windows:
                logging.debug('new window %s' % window['window_id'])
                logging.debug('adding window_name %s window_id %s' % (window['window_name'], window['window_id']))
                self._windows.append(Window.from_tmux(session=self, **window))
            return self._windows

        new = {window['window_id']: window for window in new_windows}
        old = {window._TMUX['window_id']: window for window in self._windows}
        print old
        print old.keys()

        created = set(new.keys()) - set(old.keys())
        deleted = set(old.keys()) - set(new.keys())
        intersect = set(new.keys()).intersection(set(old.keys()))

        diff = {id: dict(set(new[id].items()) - set(old[id]._TMUX.items())) for id in intersect}

        logging.info(
            "syncing windows"
            "\n\tdiff: %s\n"
            "\tcreated: %s\n"
            "\tdeleted: %s\n"
            "\tintersect: %s" % (diff, created, deleted, intersect)
        )

        for w in self._windows:
            # remove window objects if deleted or out of session
            if w._TMUX['window_id'] in deleted or self._TMUX['session_id'] != w._TMUX['session_id']:
                logging.debug("removing %s" % w)
                self._windows.remove(w)

            if w._TMUX['window_id'] in intersect:
                logging.debug('updating %s %s' % (w._TMUX['window_name'], w._TMUX['window_id']))
                w._TMUX.update(diff[w._TMUX['window_id']])

        # create window objects for non-existant window_id's
        for window in [new[window_id] for window_id in created]:
            logging.debug('new window %s' % window['window_id'])
            logging.debug('adding window_name %s window_id %s' % (window['window_name'], window['window_id']))
            self._windows.append(Window.from_tmux(session=self, **window))

        return self._windows

    def attached_window(self):
        '''
            Returns active :class:`Window` object
        '''

        for window in self.list_windows():
            if 'window_active' in window._TMUX:
                # for now window_active is a unicode
                if window._TMUX['window_active'] == '1':
                    return window
                else:
                    continue

        return False

    def select_window(self, window):
        '''
            ``tmux(1) select-window``

            window
                integer of the window index, also can be 'last-window' (-l),
                'next-window' (-n), or 'previous-window' (-p).
        '''
        tmux('select-window', '-t', window)
        self.list_windows()

    def attached_pane(self):
        '''
            Returns active :class:`Pane` object
        '''
        return self.attached_window().attached_pane()

    @property
    def windows(self):
        # check if session is based off an active tmux(1) session.
        if self._TMUX:
            return self.list_windows()
        else:
            return self._windows

    def __repr__(self):
        # todo test without session_name
        return "%s(%s)" % (self.__class__.__name__, self.session_name)


class Window(object):
    '''
    tmux window.

    Each window displayed by tmux may be split into one or more panes; each pane takes up a certain area of the
    display and is a separate terminal.  A window may be split into panes using the split-window command.  Windows
    may be split horizontally (with the -h flag) or vertically.  Panes may be resized with the resize-pane command
    (bound to 'C-up', 'C-down' 'C-left' and 'C-right' by default), the current pane may be changed with the
    select-pane command and the rotate-window and swap-pane commands may be used to swap panes without changing
    their position.  Panes are numbered beginning from zero in the order they are created.

    A number of preset layouts are available.  These may be selected with the select-layout command or cycled with
    next-layout (bound to 'Space' by default); once a layout is chosen, panes within it may be moved and resized as
    normal.

    The following layouts are supported::

    even-horizontal
        Panes are spread out evenly from left to right across the window.

    even-vertical
        Panes are spread evenly from top to bottom.

    main-horizontal
        A large (main) pane is shown at the top of the window and the remaining panes are spread from left to
        right in the leftover space at the bottom.  Use the main-pane-height window option to specify the
        height of the top pane.

    main-vertical
        Similar to main-horizontal but the large pane is placed on the left and the others spread from top to
        bottom along the right.  See the main-pane-width window option.

    tiled   Panes are spread out as evenly as possible over the window in both rows and columns.

    In addition, select-layout may be used to apply a previously used layout - the list-windows command displays
    the layout of each window in a form suitable for use with select-layout.  For example::

        $ tmux list-windows
        0: ksh [159x48]
            layout: bb62,159x48,0,0{79x48,0,0,79x48,80,0}
        $ tmux select-layout bb62,159x48,0,0{79x48,0,0,79x48,80,0}
    '''

    def __init__(self, session=None):
        self._panes = None  # list of panes
        self._session = None

        if not session:
            raise ValueError(
                "Window requires a Session object by "
                "specifying session=Session"
            )
        if not isinstance(session, Session):
            raise TypeError('session must be a Session object')

        self._session = session

    def __repr__(self):
        # todo test without session_name
        return "%s(%s %s, %s)" % (
            self.__class__.__name__,
            self._TMUX['window_index'],
            self._TMUX['window_name'],  # @todo, bug when window name blank
            self._session
        )

    def select_layout(self, layout=None):
        tmux(
            'select-layout',
            '-t%s' % self._TMUX['window_name'],      # target (name of session)
            layout
        )

    def select_pane(self, pane):
        '''
            ``tmux(1) select-pane``

            pane
                integer of the pane index, or -U, -D, -L, -R. put a konami code
        '''
        tmux('select-pane', '-t', pane)

    @live_tmux
    def split_window(self, *args, **kwargs):
        '''
        Create a new pane by splitting the window. Returns :class:`Pane`

        Used for splitting window and holding in a python object.

        Iterates ``tmux split-window``, ``-P`` to return data and
        ``-F`` for return formatting.

        @todo this could add append to the window._panes or we could
        refresh the window.list_panes() after this is ran.

        Arguments may be passed through same as ``tmux(1))`` ``split-window``.

        -h
            horizontal
        -v
            vertical

        todo:
            return :class:`Pane` object
        '''
        tmux('split-window', *args, **kwargs)

        self.list_panes()  # refresh all panes in :class:`Window`

    def attached_pane(self):
        panes = self.list_panes()

        for pane in panes:
            if 'pane_active' in pane._TMUX:
                # for now pane_active is a unicode
                if pane._TMUX['pane_active'] == '1':
                    return pane
                else:
                    continue

        return False

    @classmethod
    def from_tmux(cls, session=None, **kwargs):
        '''
        Retrieve a tmux window from server. Returns :class:`Window`

        The attributes `_panes` contains a list of :class:`Pane`

        Iterates ``tmux list-panes``, ``-F`` for return formatting.

        session
            :class:`Session` object
        '''

        if not session:
            raise ValueError(
                "Window requires a Session object by "
                "specifying session=Session"
            )
        if not isinstance(session, Session):
            raise TypeError('session must be a Session object')

        window = cls(session=session)

        window._TMUX = dict()
        for (k, v) in kwargs.items():
            window._TMUX[k] = v

        window._panes = window.list_panes()

        return window

    @live_tmux
    def list_panes(self):
        '''
            Returns a list of :class:`Pane` for the window.
        '''
        formats = ['session_name', 'session_id', 'window_index', 'window_id'] + PANE_FORMATS
        tmux_formats = ['#{%s}\t' % format for format in formats]

        panes = tmux(
            'list-panes',
            '-s',                               # for sessions
            '-t%s' % self._session.session_name,      # target (name of session)
            '-F%s' % ''.join(tmux_formats),     # output
            _iter=True                          # iterate line by line
        )

        # zip and map the results into the dict of formats used above
        panes = [dict(zip(formats, pane.split('\t'))) for pane in panes]

        # clear up empty dict
        panes = [
            dict((k, v) for k, v in pane.iteritems() if v) for pane in panes
        ]

        # filter by window_index
        panes = [
            pane for pane in panes if pane['window_index'] == self._TMUX['window_index']
        ]

        self._panes = [Pane.from_tmux(session=self._session, window=self, **pane) for pane in panes]

        return self._panes

    @property
    def panes(self):
        return self._panes


class Pane(object):
    '''
        ``tmux(1)`` pane

        ``tmux(1)`` holds a psuedoterm and linked to tmux windows.
    '''

    def __init__(self, **kwargs):
        self._session = None
        self._window = None

    @live_tmux
    def get_session(self):
        '''
        sucks
        '''
        return next((session for session in Server.list_sessions() if session._TMUX['session_name'] == self._TMUX['session_name']), None)

    @classmethod
    def from_tmux(cls, session=None, window=None, **kwargs):
        '''
        Retrieve a tmux pane from server. Returns :class:`Pane`

        Used for freezing live sessions.

        Iterates ``tmux list-panes``, ``-F`` for return formatting.

        session
            :class:`Session` object
        window
            :class:`Window` object
        '''

        if not session:
            raise ValueError('Pane generated using ``from_tmux`` must have \
                             ``Session`` object')
        else:
            if not isinstance(session, Session):
                raise TypeError('session must be a Session object')

        if not window:
            raise ValueError('Pane generated using ``from_tmux`` must have \
                             ``Window`` object')
        else:
            if not isinstance(window, Window):
                raise TypeError('window must be a Window object')

        pane = cls()

        # keep tmux variables into _TMUX
        pane._TMUX = dict()
        for (k, v) in kwargs.items():
            pane._TMUX[k] = v

        pane._session = session
        pane._window = window

        return pane

    def send_keys(self, cmd, enter=True):
        '''
            ```tmux send-keys``` to the pane

            enter
                boolean. send enter after sending the key
        '''
        tmux('send-keys', '-t', int(self._TMUX['pane_index']), cmd)

        if enter:
            self.enter()

    def enter(self):
        '''
            ```tmux send-keys``` send Enter to the pane
        '''
        tmux('send-keys', '-t', int(self._TMUX['pane_index']), 'Enter')

    def __repr__(self):
        # todo test without session_name
        return "%s(%s)" % (self.__class__.__name__, self._window)


config = kaptan.Kaptan(handler="yaml")
config.import_config("""
    windows:
        - editor:
            layout: main-vertical
            panes:
                - vim
                - cowsay "hey"
        - server: htop
        - logs: tail -f logs/development.log
    """)

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


class Server(object):
    '''
    ``t`` global. stores information on live, running tmux server

    Server.sessions [<Session>, ..]
        Session.windows [<Window>, ..]
            Window.panes [<Pane>, ..]
                Pane

    Panes, Windows and Sessions which are populated with _TMUX MetaData.

    This is an experimental design choice to just leave `-F` commands to give
    _TMUX information, decorate methods to throw an exception if it requires
    interaction with tmux

    With :attrib:`._TMUX` :class:`Session` and :class:`Window` can be accessed
    as a property, and the session and window may be looked up dynamically.

    The children inside a ``t`` object are created live. We should look into
    giving them context managers so::

        with Server.select_session(fnmatch):
            # have access to session object
            # note at this level fnmatch may have to be done via python
            # and list-sessions to retrieve object correctly
            session.la()
            with session.attached_window() as window:
                # access to current window
                pass
            with session.find_window(fnmatch) as window:
                # access to tmux matches window
                with window.attached_path() as pane:
                    # access to pane
                    pass

    '''

    def __init__(self):
        self._sessions = self.list_sessions()

    @staticmethod
    def list_sessions():
        '''
        Return a list of :class:`Session` from tmux server.

        ``tmux(1)`` ``list-sessions``
        '''
        formats = SESSION_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        sessions = tmux(
            'list-sessions',                    # ``tmux list-windows``
            '-F%s' % '\t'.join(tmux_formats),   # output
            _iter=True                          # iterate line by line
        )

        # combine format keys with values returned from ``tmux list-windows``
        sessions = [dict(zip(formats, session.split('\t'))) for session in sessions]

        # clear up empty dict
        sessions = [
            dict((k, v) for k, v in session.iteritems() if v) for session in sessions
        ]

        sessions = [Session.from_tmux(**session) for session in sessions]

        return sessions

    def has_clients(self):
        # are any clients connected to tmux
        if len(tmux('list-clients')) > 1:
            return True
        else:
            return False

    def attached_sessions(self):
        '''
            Returns active :class:`Session` object

            This will not work where multiple tmux sessions are attached.
        '''

        if not self._sessions:
            return None

        sessions = self._sessions
        attached_sessions = list()

        for session in sessions:
            if 'session_attached' in session._TMUX:
                # for now session_active is a unicode
                if session._TMUX['session_attached'] == '1':
                    logging.info('session %s attached', session.session_name)
                    attached_sessions.append(session)
                else:
                    continue

        return attached_sessions or None

    def has_session(self, session_name):
        '''
        ``tmux(1)`` ``has-session``
        '''

        # has-session returns nothing if session exists
        try:
            tmux('has-session', '-t', session_name)
            return True
        except ErrorReturnCode_1 as e:
            return False

    def kill_session(self, session_name):
        '''
        ``tmux(1)`` ``kill-session``

        session_name
            string. note this accepts fnmatch(3).  'asdf' will kill asdfasd
        '''
        try:
            tmux('kill-session', '-t', session_name)
        except ErrorReturnCode_1 as e:
            logging.error(
                "\n\tcmd:\t%s\n"
                "\terror:\t%s"
                % (e.full_cmd, e.stderr)
            )
            return False

    @property
    def sessions(self):
        return self._sessions

    def list_clients(self):
        raise NotImplemented

    def switch_client(self, target_session):
        '''
        ``tmux(1) ``switch-client``

        target_session
            string. name of the session. fnmatch(3) works
        '''
        tmux('switch-client', '-t', target_session)

#for session in Server.list_sessions():
#    for window in session.windows:
#        for pane in window.panes:
#            pass

t = Server()
