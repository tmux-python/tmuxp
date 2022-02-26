from .test_plugin_helpers import MyTestTmuxpPlugin


class AllVersionPassPlugin(MyTestTmuxpPlugin):
    def __init__(self):
        config = {
            "plugin_name": "tmuxp-plugin-my-tmuxp-plugin",
            "tmux_min_version": "1.8",
            "tmux_max_version": "100.0",
            "tmux_version_incompatible": ["2.3"],
            "libtmux_min_version": "0.8.3",
            "libtmux_max_version": "100.0",
            "libtmux_version_incompatible": ["0.7.1"],
            "tmuxp_min_version": "1.7.0",
            "tmuxp_max_version": "100.0.0",
            "tmuxp_version_incompatible": ["1.5.6"],
            "tmux_version": "3.0",
            "tmuxp_version": "1.7.0",
        }
        MyTestTmuxpPlugin.__init__(self, config)
