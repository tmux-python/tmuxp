from .test_plugin_helpers import TestTmuxpPluginInterface


class TmuxpVersionFailMinPlugin(TestTmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'tmuxp-min-verion-fail',
            'tmuxp_min_version': '1.6.0',
            'tmuxp_version': '1.5.6'
        }
        TestTmuxpPluginInterface.__init__(self, config)


class TmuxpVersionFailMaxPlugin(TestTmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'tmuxp-max-verion-fail',
            'tmuxp_min_version': '2.0.0',
            'tmuxp_version': '2.5'
        }
        TestTmuxpPluginInterface.__init__(self, config)


class TmuxpVersionFailIncompatiblePlugin(TestTmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'tmuxp-incompatible-verion-fail',
            'tmuxp_version_incompatible': ['1.5.0'],
            'tmuxp_version': '1.5.0'
        }
        TestTmuxpPluginInterface.__init__(self, config)