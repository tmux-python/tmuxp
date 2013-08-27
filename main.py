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

windows = list()
for window in config.get('windows'):
    #pprint(window)

    """expand
        dict({'session_name': { dict })

        to

        dict({ name='session_name', **dict})
    """
    if len(window) == 1:
        name = window.iterkeys().next() # get window name

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

pprint(tmux('list-windows'))
pprint(windows)


