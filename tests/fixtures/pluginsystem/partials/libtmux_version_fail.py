from .test_plugin_helpers import MyTestTmuxpPluginInterface


class LibtmuxVersionFailMinPlugin(MyTestTmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'libtmux-min-version-fail',
            'libtmux_min_version': '0.8.3',
            'libtmux_version': '0.7.0',
        }
        MyTestTmuxpPluginInterface.__init__(self, config)


class LibtmuxVersionFailMaxPlugin(MyTestTmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'libtmux-max-version-fail',
            'libtmux_max_version': '3.0',
            'libtmux_version': '3.5',
        }
        MyTestTmuxpPluginInterface.__init__(self, config)


class LibtmuxVersionFailIncompatiblePlugin(MyTestTmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'libtmux-incompatible-version-fail',
            'libtmux_version_incompatible': ['0.7.1'],
            'libtmux_version': '0.7.1',
        }
        MyTestTmuxpPluginInterface.__init__(self, config)
