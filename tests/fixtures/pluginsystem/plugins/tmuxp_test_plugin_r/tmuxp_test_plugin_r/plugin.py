from tmuxp.plugin import TmuxpPlugin


class PluginReattach(TmuxpPlugin):
    def __init__(self):
        self.message = '[+] This is the Tmuxp Test Plugin'

    def reattach(self, session):
        session.rename_session('plugin_test_r')
