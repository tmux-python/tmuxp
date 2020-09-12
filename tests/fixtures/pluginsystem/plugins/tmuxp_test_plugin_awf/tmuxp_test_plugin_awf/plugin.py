from tmuxp_plugin_interface.plugin import TmuxpPluginInterface

class PluginAfterWindowFinished(TmuxpPluginInterface):
    def __init__(self):
        self.message = f'[+] This is the Tmuxp Test Plugin'

    def after_window_finished(self, window):  
        pass