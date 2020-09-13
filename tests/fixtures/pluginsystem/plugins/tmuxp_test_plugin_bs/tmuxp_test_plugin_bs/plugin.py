from tmuxp_plugin_interface.plugin import TmuxpPluginInterface

class PluginBeforeScript(TmuxpPluginInterface):
    def __init__(self):
        self.message = f'[+] This is the Tmuxp Test Plugin'

    def before_script(self, session):
        print('Changing session_name to plugin_test_bs')
        session.rename_session('plugin_test_bs')