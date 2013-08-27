import kaptan
from sh import tmux
from pprint import pprint

config = kaptan.Kaptan(handler="yaml")

config.import_config("""
windows:
  - editor:
      layout: main-vertical
      panes:
        - vim
        - guard
  - server: bundle exec rails s
  - logs: tail -f logs/development.log
""")

print config
pprint(config.__dict__)

"""
    tmux wrapper was invented to solve the panes / pains of managing workspaces

    hierarchy:

    session(s)
        - cmds (str like 'htop' or list ['pwd', 'htop'])
        - root (str dir path, like '/var/www')
        - window(s)
            - cmd(s)
            - root
            - panes(s)
                - dimensions
                - cmd(s)
                - root

    cmd, cwd can be added at the session, window and pane level.

    the deepest will have precedence. a command or cwd at the session level
    will apply to all windows, panes within it. a command or cwd at window
    level applies to all panes. a pane may specify its own cmd.

    advanced sorcery:
        before_cmd / after_cmd:

        tbd, but commands will be able to be go before/after commands on any
        level also. for instance, session may run before_cmd: and all windows
        and panes within will run accordingly

        aliases:

        a common command may be aliased as a shortcut to prevent duplication.
        syntax for this is still subject to change

    behind the hood:
        the code is very simple. kaplan will read any type of config file and
        turn it into a python dictionary. for brevity, tmuxwrapper offers a
        few short forms, such as (in YAML):

        mywindow: my_cmd

        which is expanded to:

        {
            name: 'mywindow',
            panes: [
                cmds: ['my_cmd']
            ]
        }

        Session, Window, Pane are all python classes which accept options and
        print out as a __dict__ and __cmd__.

        __dict__ : dict : a fully expanded python dictionary configuration for
        the object.
        to_json(): str : export the object to JSON config format
        to_yaml(): str : export the object to YAML config
        to_ini(): str : export object to INI config

        How a session is built:

            A Session object holds Window(s)
            A Window holds Panes

        They are meant to provide a clear abstraction of tmux's api.

        How do the panes / windows accept configuration from windows and
        sessions?

        A Session() object may be created by itself, but the __init__ will
        check for a Window object and Session object. This assures that Windows
        and Panes can inherit the cmd's, root dirs and before_cmd and
        after_cmd.

    Roadmap:

        To a degree, be able to pull running tmux sessions, windows and panes
        into Session, Window, and Pane objects and therefore be exportable
        into configs.

        A la, many attempts before, a pip freeze.

        The biggest difficulty is keeping the abstraction of tmux pure and
        pythonic.

"""

windows = list()
"""expand inline configuration """
for window in config.get('windows'):
    """expand
        dict({'session_name': { dict })

        to

        dict({ name='session_name', **dict})
    """

    if len(window) == 1:
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
        if len(window['panes']) > 1:
            pprint('omg multiple panes')

    windows.append(window)


class Session(object):
    __FORMATS__ = [
        'session_attached', 'session_created', 'session_created_string',
        'session_group', 'session_grouped', 'session_height', 'session_id',
        'session_name', 'session_width', 'session_windows']

    pass


class Window(object):
    pass


class Pane(object):
    pass


pprint(tmux('list-windows'))
pprint(windows)
