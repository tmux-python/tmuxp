"""
    tmuxwrapper
    ~~~~~~~~~~~

    tmuxwrapper helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock <tony@git-pull.com>.
    :license: BSD, see LICENSE for details
"""
import kaptan
from sh import tmux, cut, ErrorReturnCode_1
from pprint import pprint
from formats import SESSION_FORMATS, WINDOW_FORMATS, PANE_FORMATS


class SessionExists(Exception):
    pass


class Session(object):
    '''
    tmux session
    '''

    def __init__(self, **kwargs):
        if 'session_name' not in kwargs:
            raise ValueError('Session requires session_name')
        else:
            for (k, v) in kwargs.items():
                setattr(self, k, v)

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
        if not len(tmux('has-session', '-t', session_name)):
            try:

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

        formats = WINDOW_FORMATS
        tmux_formats = ['#{%s}' % format for format in formats]

        windows = tmux(
            'list-windows',                     # ``tmux list-windows``
            '-t%s' % kwargs['session_name'],    # target (session name)
            '-F%s' % '\t'.join(tmux_formats),   # output
            _iter=True                          # iterate line by line
        )

        # combine format keys with values returned from ``tmux list-windows``
        windows = [dict(zip(formats, window.split('\t'))) for window in windows]

        # clear up empty dict
        windows = [
            dict((k, v) for k, v in window.iteritems() if v) for window in windows
        ]

        session._windows = [Window.from_tmux(session=session, **window) for window in windows]

        pprint('%s, windows for %s' % (
            len(session._windows),
            kwargs['session_name']
        ))
        pprint(session._windows)

        return session

    @property
    def windows(self):
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

    def __init__(self, **kwargs):

        if 'session' in kwargs:
            self._panes = None
            if isinstance(kwargs['session'], Session):
                self._session = kwargs['session']
            else:
                raise TypeError('session must be a Session object')

        [setattr(self, k, v) for (k, v) in kwargs.items() if k is not 'session']

    def __repr__(self):
        # todo test without session_name
        return "%s(%s %s, %s)" % (
            self.__class__.__name__,
            self._TMUX['window_index'],
            self._TMUX['window_name'],
            self._session
        )

    __LAYOUTS__ = [
        'even-horizontal',  # Panes are spread out evenly from left to right across the window.
        'even-vertical',    # Panes are spread evenly from top to bottom.
        'main-horizontal',
        'main-vertical',
        'tiled'
    ]

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

        formats = PANE_FORMATS + WINDOW_FORMATS
        tmux_formats = ['#{%s}\t' % format for format in formats]

        panes = tmux(
            'list-panes',
            '-s',                               # for sessions
            '-t%s' % session.session_name,      # target (name of session)
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
            pane for pane in panes if pane['window_index'] == window._TMUX['window_index']
        ]

        #pprint(panes)

        window._panes = [Pane.from_tmux(session=session, window=window, **pane) for pane in panes]

        pprint('%s, panes for %s' % (
            len(window._panes),
            kwargs['window_index']
        ))
        pprint(window._panes)

        return window

    @property
    def panes(self):
        return self._panes


class Pane(object):

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

    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        # todo test without session_name
        return "%s(%s)" % (self.__class__.__name__, self._window)


def get_sessions():
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

    for session in sessions:
        yield session


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


for session in get_sessions():
    for window in session.windows:
        for pane in window.panes:
            pass

tmux('switch-client', '-t0')
tmux('switch-client', '-ttony')

TEST_SESSION_NAME = 'tmuxwrapper_dev'

session = Session.new_session(
    session_name=TEST_SESSION_NAME,
    kill_session=True
)
#tmux('new-session', '-d', '-s', TEST_SESSION_NAME)
tmux('switch-client', '-t', TEST_SESSION_NAME)

tmux('split-window', '-h', '-p30')
#tmux('send-keys', '-t', 'cd /srv/www/flaskr')
tmux('split-window', '-v', '-p50')
tmux('split-window', '-v', '-p50')
tmux('display-panes')
