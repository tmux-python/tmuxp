import kaptan
from sh import tmux, cut
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

windows = list()
# expand inline window configuration
""" expand
    dict({'session_name': { dict })

    to

    dict({ name='session_name', **dict})
"""

for window in config.get('windows'):

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

    def __init__(self, session_name):
        self._session_name = session_name

    @property
    def session_name(self):
        return self._session_name

    def __repr__(self):
        return "%s(%s)" % (self.__class__, self.session_name)

    pass


class Window(object):
    pass


class Pane(object):
    pass


pprint(tmux('list-windows'))
pprint(windows)

def list_sessions():
    for session in cut(tmux('list-sessions'), '-f1', '-d:'):
        yield Session(session.strip('\n'))

pprint(list(list_sessions()))
