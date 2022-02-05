from tmuxp.plugin import TmuxpPlugin


class PluginBeforeScript(TmuxpPlugin):
    def __init__(self):
        self.message = '[+] This is the Tmuxp Test Plugin'

    def before_script(self, session):
        session.rename_session('plugin_test_bs')
