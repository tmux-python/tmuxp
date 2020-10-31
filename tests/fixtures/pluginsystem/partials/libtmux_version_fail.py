from .test_plugin_helpers import MyTestTmuxpPlugin


class LibtmuxVersionFailMinPlugin(MyTestTmuxpPlugin):
    def __init__(self):
        config = {
            'plugin_name': 'libtmux-min-version-fail',
            'libtmux_min_version': '0.8.3',
            'libtmux_version': '0.7.0',
        }
        MyTestTmuxpPlugin.__init__(self, config)


class LibtmuxVersionFailMaxPlugin(MyTestTmuxpPlugin):
    def __init__(self):
        config = {
            'plugin_name': 'libtmux-max-version-fail',
            'libtmux_max_version': '3.0',
            'libtmux_version': '3.5',
        }
        MyTestTmuxpPlugin.__init__(self, config)


class LibtmuxVersionFailIncompatiblePlugin(MyTestTmuxpPlugin):
    def __init__(self):
        config = {
            'plugin_name': 'libtmux-incompatible-version-fail',
            'libtmux_version_incompatible': ['0.7.1'],
            'libtmux_version': '0.7.1',
        }
        MyTestTmuxpPlugin.__init__(self, config)
