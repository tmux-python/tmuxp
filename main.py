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

    ``MetaData`` or the ``._TMUX`` attribute in objects
        information ``tmux(1)`` returns on certain commands listing or creating
        sessions, windows nad panes.

    session
        used by ``tmux(1)`` to hold windows, panes. its' counterpart is
        :class:`Session` object.

    window
        used by ``tmux(1) to hold panes. a freshly created window only has one
        pane. ``tmux(1)``'s ``split-window`` can create panes horizontally
        or vertically. represented by :class:`Window`

    pane
        an individual pseudo terminal / shell prompt. represented by the
        :class:`Pane` object.

    :meth:`from_tmux`
        pulls information from a live tmux server.

    Magic
        the ``MetaData`` in ``._TMUX`` attributes on :class:`Session`,
        :class:`Window` and :class:`Pane` objects is used to pull a reference
        from a global object. :attrib:`._session` and :attrib:`._window`
        in ``Window`` and ``Pane`` are properties that forward to that.

    Which tmux client is used?
        tmux allows for multiple clients and sessions. ``tmuxwrapper`` will
        interact with the most recently attached client you attached. When
        testing, just run a ``tmux`` in shell and do what you have to do.

"""
import kaptan
from sh import tmux as tmx, cut, ErrorReturnCode_1
from pprint import pprint
from formats import SESSION_FORMATS, WINDOW_FORMATS, PANE_FORMATS
from functools import wraps


def tmux(*args, **kwargs):
    '''
    wrap tmux from ``sh`` library in a try catch
    '''
    try:
        return tmx(*args, **kwargs)
    except ErrorReturnCode_1 as e:
        pprint(e)
        pass


def live_tmux(f):
    '''
    decorator that checks for :attrib:`._TMUX` inside :class:`.Session`,
    :class:`.Window` and :class:`.Pane` objects.

    :attrib:`._TMUX` stores valuable information for an tmux object's life
    cycle. Hereinafter, I will call this ``MetaData``.

    ``tmux( returns information

    @todo: in the future, :class:`Pane` will have ``PANE_FORMATS``,
    ``WINDOW_FORMATS`` and ``SESSION_FORMATS`` metadata, and :class:`Window`
    will have ``WINDOW_FORMATS`` and ``SESSION_FORMATS``. If a :attrib:`._TMUX
    exists, it should be possible to do a lookup for its parent :class:`Window`
    or :class:`Pane` object.

    Because this data is live in the system, caching strategy isn't a priority.

    If a session is imported directly from a configuration or is otherwise
    being built manually via CLI or scripting, :attrib:`._TMUX` is populated
    when:

    A tmux session is created with:

    :meth:`Session.create_session` aka ``tmux create-session``

    :meth:`Session.list_sessions` aka ``tmux list-sessions``
    :meth:`Session.new_window` aka ``tmux new-window``
    :meth:`Window.split_window` aka ``tmux split-window``
        returns a :class:`Pane` with pane metadata

        - its first :class:`Window`, in :attrib:`._windows`, and subsequently,
          and the :class:`Window`'s first :class:`.Pane` in :attrib:`._panes`
          is populated with :attrib:`._TMUX`. This is returned because the

            attributes.
        - a window is created with :meth:`Session.create_session`.
    '''
    def live_tmux(self):
        if not self._TMUX:
            raise NotRunning(
                "self._TMUX not found, this object is not part of an active"
                "tmux session. If you need help please post an issue on github"
            )
        return f(self)
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

    session_name = None

    def __init__(self, **kwargs):
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
        Equivalent to ``tmux new-session`` Returns :class:`.Session`.

        Uses ``-P`` flag to print session info, ``-F`` for return formatting
        returns new Session object

        kill_session
            Kill current session if ``tmux has-session``. Useful for testing
            workspaces.
        '''
        try:
            if not len(tmux('has-session', '-t', session_name)):
                if kill_session:
                    tmux('kill-session', '-t', session_name)
                    pprint('session %s exists. killed it.' % session_name)
                else:
                    raise SessionExists('Session named %s exists' % session_name)
        except ErrorReturnCode_1:
            pass

        pprint('creating session')

        formats = SESSION_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        session_info = tmux(
            'new-session',
            '-d',
            '-s', TEST_SESSION_NAME,
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

    @classmethod
    def from_tmux(cls, **kwargs):
        '''
        Freeze of the current tmux session directly from the server. Returns
        :class:`.Session`.

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

    @classmethod
    def list_sessions(cls):
        '''
        Return a list of :class:`.Session`. from tmux server.

        Uses ``tmux list-sessions``.
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

        sessions = [cls.from_tmux(**session) for session in sessions]

        for session in sessions:
            yield session

    def list_windows(self):
        '''
        Return a list of :class:`.Window` inside the tmux session
        '''
        formats = WINDOW_FORMATS
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

        pprint('%s, windows for %s' % (
            len(windows),
            self.session_name
        ))
        # pprint(windows)

        windows = [Window.from_tmux(session=self, **window) for window in windows]
        return windows

    def active_window(self):
        '''
            Returns active :class:`.Window` object
        '''
        windows = self.list_windows()

        for window in windows:
            pprint(window._TMUX)
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

    def active_pane(self):
        '''
            Returns active :class:`.Pane` object
        '''
        return self.active_window().active_pane()

    @property
    def windows(self):
        # check if this object is based off an active session, use _TMUX for
        # now.
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

    _panes = None

    def __init__(self, session=None):
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

    __LAYOUTS__ = [
        'even-horizontal',  # Panes are spread out evenly from left to right across the window.
        'even-vertical',    # Panes are spread evenly from top to bottom.
        'main-horizontal',
        'main-vertical',
        'tiled'
    ]

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

    def active_pane(self):
        panes = self.list_panes()

        for pane in panes:
            pprint(pane._TMUX)
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
        Retrieve a tmux window from server. Returns :class:`.Window`.

        The attributes `_panes` contains a list of :class:`.Pane`

        Iterates ``tmux list-panes``, ``-F`` for return formatting.

        session
            :class:`.Session` object
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

        pprint(type(window._panes))
        pprint('%s, panes for %s' % (
            len(window._panes),
            kwargs['window_index']
        ))
        pprint(window._panes)

        return window

    @live_tmux
    def list_panes(self):
        '''
            Returns a list of :class:`.Pane` for the window.
        '''
        formats = PANE_FORMATS + WINDOW_FORMATS
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
    '''

    @classmethod
    def split_window(cls, session=None, window=None, **kwargs):
        '''
        Create a new pane by splitting the window. Returns :class:`.Pane`.

        Used for splitting window and holding in a python object.

        Iterates ``tmux split-window``, ``-P`` to return data and
        ``-F`` for return formatting.

        session
            :class:`.Session` object
        window
            :class:`.Window` object
        '''
        raise NotImplemented

    @classmethod
    def from_tmux(cls, session=None, window=None, **kwargs):
        '''
        Retrieve a tmux pane from server. Returns :class:`.Pane`.

        Used for freezing live sessions.

        Iterates ``tmux list-panes``, ``-F`` for return formatting.

        session
            :class:`.Session` object
        window
            :class:`.Window` object
        '''

        if not session:
            raise ValueError('Pane generated using ``.from_tmux`` must have \
                             ``Session`` object')
        else:
            if not isinstance(session, Session):
                raise TypeError('session must be a Session object')

        if not window:
            raise ValueError('Pane generated using ``.from_tmux`` must have \
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

    def __init__(self, **kwargs):
        pass

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
    holds information on live, running tmux server

    Server.sessions [<Session>, ..]
        Session.windows [<Window>, ..]
            Window.panes [<Pane>, ..]
                Pane

    '''
    def list_sessions(self):
        pass

    @property
    def sessions(self):
        raise NotImplemented

    def list_clients(self):
        raise NotImplemented


t = Server()


for session in Session.list_sessions():
    for window in session.windows:
        for pane in window.panes:
            pass


tmux('switch-client', '-t0')
tmux('switch-client', '-ttony')
tmux('switch-client', '-ttonsy')

TEST_SESSION_NAME = 'tmuxwrapper_dev'

session = Session.new_session(
    session_name=TEST_SESSION_NAME,
    kill_session=True
)
tmux('switch-client', '-t', TEST_SESSION_NAME)

# bash completion
# allow  tmuxwrapper to export split-pane,  key bindings

tmux('split-window')
session.active_window().select_layout('even-horizontal')
tmux('split-window')

tmux('new-window')
session.select_window(1)

#session.active_window().select_layout('even-vertical')
#pprint(session.active_window()._panes[0]._TMUX['pane_index'])
#pprint(session.active_window().active_pane())

session.active_window().select_pane(1)
session.active_pane().send_keys('cd /srv/www/flaskr')
session.active_window().select_pane(0)

#pprint(dir(tmux))
#session.send_keys()   send to all? or active pane?
#session.send_keys(all=True) send to all windows + panes?
tmux('display-panes')
