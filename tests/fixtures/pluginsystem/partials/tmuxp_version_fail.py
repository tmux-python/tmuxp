from .test_plugin_helpers import MyTestTmuxpPlugin


class TmuxpVersionFailMinPlugin(MyTestTmuxpPlugin):
    def __init__(self):
        config = {
            "plugin_name": "tmuxp-min-version-fail",
            "tmuxp_min_version": "1.7.0",
            "tmuxp_version": "1.6.3",
        }
        MyTestTmuxpPlugin.__init__(self, config)


class TmuxpVersionFailMaxPlugin(MyTestTmuxpPlugin):
    def __init__(self):
        config = {
            "plugin_name": "tmuxp-max-version-fail",
            "tmuxp_max_version": "2.0.0",
            "tmuxp_version": "2.5",
        }
        MyTestTmuxpPlugin.__init__(self, config)


class TmuxpVersionFailIncompatiblePlugin(MyTestTmuxpPlugin):
    def __init__(self):
        config = {
            "plugin_name": "tmuxp-incompatible-version-fail",
            "tmuxp_version_incompatible": ["1.5.0"],
            "tmuxp_version": "1.5.0",
        }
        MyTestTmuxpPlugin.__init__(self, config)
