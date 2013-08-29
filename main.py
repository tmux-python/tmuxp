import kaptan
from sh import tmux, cut
from pprint import pprint


class Session(object):

    def __init__(self, **kwargs):
        if 'session_name' not in kwargs:
            raise ValueError('Session requires session_name')
        else:
            for (k, v) in kwargs.items():
                setattr(self, k, v)


    @property
    def windows(self):
        """
            ``tmux list-windows`` outputs 1 session per line ``\n``.

            -F (FORMATS) allows returning custom sessings, we delimit with
            a tab ``\t``.

            we then use dict+zip to align the format variable with the
            output.

            the ``Window`` object accepts the returned properties  and
            ``Session`` (``self``) object.
        """

        if hasattr(self, 'session_name'):
            formats = WINDOW_FORMATS
            tmux_formats = ['#{%s}\t' % format for format in formats]

            windows = cut(
                tmux(
                    'list-windows',                 # ``tmux list-windows``
                    '-t%s' % self.session_name,     # target (session name)
                    '-F%s' % ''.join(tmux_formats)  # output
                ), '-f1', '-d:'
            )

            # combine format keys with values returned from ``tmux list-windows``
            windows = [dict(zip(formats, window.split('\t'))) for window in windows]

            # clear up empty dict
            windows = [
                dict((k, v) for k, v in window.iteritems() if v) for window in windows
            ]

            windows = [Window(session=self, **window) for window in windows]

            return windows
        else:
            return None  # session is not bound to a current session, the user
                         # is using Session imported config file to launch a
                         # new session

    def __repr__(self):
        # todo test without session_name
        return "%s(%s)" % (self.__class__, self.session_name)


class Window(object):
    """
        todo
            - @has_session property, or throw an Error
            - Pane
            - __cmd__
    """

    """
     Each window displayed by tmux may be split into one or more panes; each pane takes up a certain area of the
     display and is a separate terminal.  A window may be split into panes using the split-window command.  Windows
     may be split horizontally (with the -h flag) or vertically.  Panes may be resized with the resize-pane command
     (bound to 'C-up', 'C-down' 'C-left' and 'C-right' by default), the current pane may be changed with the
     select-pane command and the rotate-window and swap-pane commands may be used to swap panes without changing
     their position.  Panes are numbered beginning from zero in the order they are created.

     A number of preset layouts are available.  These may be selected with the select-layout command or cycled with
     next-layout (bound to 'Space' by default); once a layout is chosen, panes within it may be moved and resized as
     normal.

     The following layouts are supported:

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
     the layout of each window in a form suitable for use with select-layout.  For example:

           $ tmux list-windows
           0: ksh [159x48]
               layout: bb62,159x48,0,0{79x48,0,0,79x48,80,0}
           $ tmux select-layout bb62,159x48,0,0{79x48,0,0,79x48,80,0}



    """
    def __init__(self, **kwargs):

        if 'session' in kwargs:
            if isinstance(kwargs['session'], Session):
                self._session = kwargs['session']
            else:
                raise TypeError('session must be a Session object')

        [setattr(self, k, v) for (k, v) in kwargs.items() if k is not 'session']

    def __repr__(self):
        # todo test without session_name
        return "%s(%s)" % (self.__class__, self.__dict__)

    __LAYOUTS__ = [
        'even-horizontal',  # Panes are spread out evenly from left to right across the window.
        'even-vertical',  # Panes are spread evenly from top to bottom.
        'main-horizontal',
        'main-vertical',
        'tiled'
    ]

    def from_tmux(self):
        """ parse into normal properties """
        pass

    def to_cmd(self):
        """ parse into tmux cmd to recreate workspace panes """
        pass

    # __dict__ should return properties that would export into a config

    @property
    def __cmd__(self):
        for pane in self.panes:
            pprint(pane.__dict__)

    @property
    def session(self):
        # remove this?
        return self._session if self._session else None

    @property
    def panes(self):
        """
            ``tmux list-panes`` outputs 1 session per line ``\n``.

            -F (FORMATS) picks settings return, we delimit with tab ``\t``.

            we then use dict+zip to align the format variable with the
            output.

            the ``Pane`` object accepts the returned properties, ``Session``
            object and ``Window`` (``self``) object.
        """

        if hasattr(self.session, 'session_name'):
            formats = PANE_FORMATS
            tmux_formats = ['#{%s}\t' % format for format in formats]

            panes = cut(
                tmux(
                    'list-panes',
                    '-s',                                # for sessions
                    '-t%s' % self.session.session_name,  # target (name of session)
                    '-F%s' % ''.join(tmux_formats)       # output
                ), '-f1', '-d:'
            )

            # `tmux list-panes` outputs a session per-line,
            # separate every line from `tmux list-panes` into a pane
            panes = str(panes).split('\n')

            # zip and map the results into the dict of formats used above
            panes = [dict(zip(formats, pane.split('\t'))) for pane in panes]

            # clear up empty dict
            panes = [
                dict((k, v) for k, v in pane.iteritems() if v) for pane in panes
            ]

            panes = [Pane.from_tmux(session=self.session, window=self, **pane) for pane in panes]

            return panes


class Pane(object):

    @classmethod
    def from_tmux(cls, **kwargs):
        """ return a Pane object
            arguments are results passed from tmux
        """
        pane = cls()

        for (k, v) in kwargs.items():
            setattr(pane, k, v)

        # verify Session object
        if 'session' in kwargs:
            if isinstance(kwargs['session'], Session):
                pane._session = kwargs['session']
            else:
                raise TypeError('session must be a Session object')

        # verify Window object
        if 'window' in kwargs:
            if isinstance(kwargs['window'], Window):
                pane._window = kwargs['window']
            else:
                raise TypeError('window must be a Window object')

        return pane


    def __init__(self, **kwargs):
        pass


    def __repr__(self):
        # todo test without session_name
        return "%s(%s)" % (self.__class__, self.__dict__)


def get_sessions():
    formats = SESSION_FORMATS
    tmux_formats = ['#{%s}\t' % format for format in formats]

    sessions = cut(
        tmux(
            'list-sessions',                 # ``tmux list-windows``
            '-F%s' % ''.join(tmux_formats)  # output
        ), '-f1', '-d:'
    )

    # combine format keys with values returned from ``tmux list-windows``
    sessions = [dict(zip(formats, session.split('\t'))) for session in sessions]

    # clear up empty dict
    sessions = [
        dict((k, v) for k, v in session.iteritems() if v) for session in sessions
    ]

    sessions = [Session(**session) for session in sessions]

    for session in sessions:
        yield session


"""
    experiment, ALL_FORMATS parsing for session, window, pane object and
    remove blank values

    http://sourceforge.net/p/tmux/tmux-code/ci/master/tree/format.c
"""

SESSION_FORMATS = [
    'session_group',
    'session_name',
    'session_windows',
    'session_width',
    'session_height',
    'session_id',
    'session_grouped',
    'session_group',
    'session_created',
    'session_created_string',
    'session_attached',
]

CLIENT_FORMATS = [
    'client_cwd',
    'client_height',
    'client_width',
    'client_tty',
    'client_termname',
    'client_created',
    'client_created_string',
    'client_activity',
    'client_activity_string',
    'client_prefix',
    'client_utf8',
    'client_readonly',
    'client_session',
    'client_last_session',
]

WINDOW_FORMATS = [
    # format_window()
    'window_id',
    'window_name',
    'window_width',
    'window_height',
    'window_layout',
    'window_panes',
    # format_winlink()
    'window_index',
    'window_flags',
    'window_active',
    'window_bell_flag',
    'window_activity_flag',
    'window_silence_flag',
]

PANE_FORMATS = [
    'history_size',
    'history_limit',
    'history_bytes',
    'pane_index',
    'pane_width',
    'pane_height',
    'pane_title',
    'pane_id',
    'pane_active',
    'pane_dead',
    'pane_in_mode',
    'pane_synchronized',
    'pane_tty',
    'pane_pid',
    'pane_start_command',
    'pane_start_path',
    'pane_current_path',
    'pane_current_command',

    'cursor_x',
    'cursor_y',
    'scroll_region_upper',
    'scroll_region_lower',
    'saved_cursor_x',
    'saved_cursor_y',

    'alternate_on',
    'alternate_saved_x',
    'alternate_saved_y',

    'cursor_flag',
    'insert_flag',
    'keypad_cursor_flag',
    'keypad_flag',
    'wrap_flag',

    'mouse_standard_flag',
    'mouse_button_flag',
    'mouse_any_flag',
    'mouse_utf8_flag',
]


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

print config
pprint(config.__dict__)
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
            pprint('omg multiple panes')

    windows.append(window)


for session in get_sessions():
    #pprint(session)
    for window in session.windows:
        #pprint(window)
        pprint(window.__cmd__)

        for pane in window.panes:
            #pprint(pane.__dict__)
            pass
