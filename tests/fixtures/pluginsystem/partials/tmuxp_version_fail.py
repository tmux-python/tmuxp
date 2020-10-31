from .test_plugin_helpers import MyTestTmuxpPluginInterface


class TmuxpVersionFailMinPlugin(MyTestTmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'tmuxp-min-version-fail',
            'tmuxp_min_version': '1.6.0',
            'tmuxp_version': '1.5.6',
        }
        MyTestTmuxpPluginInterface.__init__(self, config)


class TmuxpVersionFailMaxPlugin(MyTestTmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'tmuxp-max-version-fail',
            'tmuxp_max_version': '2.0.0',
            'tmuxp_version': '2.5',
        }
        MyTestTmuxpPluginInterface.__init__(self, config)


class TmuxpVersionFailIncompatiblePlugin(MyTestTmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'tmuxp-incompatible-version-fail',
            'tmuxp_version_incompatible': ['1.5.0'],
            'tmuxp_version': '1.5.0',
        }
        MyTestTmuxpPluginInterface.__init__(self, config)
