from .test_plugin_helpers import MyTestTmuxpPlugin


class TmuxVersionFailMinPlugin(MyTestTmuxpPlugin):
    def __init__(self):
        config = {
            'plugin_name': 'tmux-min-version-fail',
            'tmux_min_version': '1.8',
            'tmux_version': '1.7',
        }
        MyTestTmuxpPlugin.__init__(self, config)


class TmuxVersionFailMaxPlugin(MyTestTmuxpPlugin):
    def __init__(self):
        config = {
            'plugin_name': 'tmux-max-version-fail',
            'tmux_max_version': '3.0',
            'tmux_version': '3.5',
        }
        MyTestTmuxpPlugin.__init__(self, config)


class TmuxVersionFailIncompatiblePlugin(MyTestTmuxpPlugin):
    def __init__(self):
        config = {
            'plugin_name': 'tmux-incompatible-version-fail',
            'tmux_version_incompatible': ['2.3'],
            'tmux_version': '2.3',
        }

        MyTestTmuxpPlugin.__init__(self, config)
