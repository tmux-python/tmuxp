from tmuxp_plugin_interface.plugin import TmuxpPluginInterface

class PluginReattach(TmuxpPluginInterface):
    def __init__(self):
        self.message = f'[+] This is the Tmuxp Test Plugin'

    def reattach(self, session):
        session.rename_session('plugin_test_r')
