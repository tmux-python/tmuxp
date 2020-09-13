from tmuxp_plugin_interface.plugin import TmuxpPluginInterface

class PluginOnWindowCreate(TmuxpPluginInterface):
    def __init__(self):
        self.message = f'[+] This is the Tmuxp Test Plugin'

    def on_window_create(self, window):
        if window.name == 'editor': 
            window.rename_window('plugin_test_owc')