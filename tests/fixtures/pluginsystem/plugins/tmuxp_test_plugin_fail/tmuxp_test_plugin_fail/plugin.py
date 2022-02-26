from tmuxp.plugin import TmuxpPlugin


class PluginFailVersion(TmuxpPlugin):
    def __init__(self):
        config = {
            "plugin_name": "tmuxp-plugin-fail-version",
            "tmuxp_max_version": "0.0.0",
        }
        TmuxpPlugin.__init__(self, **config)
