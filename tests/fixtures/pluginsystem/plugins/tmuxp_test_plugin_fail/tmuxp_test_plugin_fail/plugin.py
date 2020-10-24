from tmuxp.plugin import TmuxpPluginInterface


class PluginFailVersion(TmuxpPluginInterface):
    def __init__(self):
        config = {
            'plugin_name': 'tmuxp-plugin-fail-version',
            'tmuxp_max_version': '0.0.0',
        }
        TmuxpPluginInterface.__init__(self, **config)