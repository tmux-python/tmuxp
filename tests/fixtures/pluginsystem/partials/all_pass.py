from .test_plugin_helpers import TestTmuxpPluginInterface


class AllVersionPassPlugin(TestTmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'tmuxp-plugin-my-tmuxp-plugin',
            'tmux_min_version': '1.8',
            'tmux_max_version': '100.0',
            'tmux_version_incompatible': ['2.3'],
            'tmuxp_min_version': '1.6.0',
            'tmuxp_max_version': '100.0.0',
            'tmuxp_version_incompatible': ['1.5.6'],
            'tmux_version': '3.0',
            'tmuxp_version': '1.6.0',
        }
        TestTmuxpPluginInterface.__init__(self, config)