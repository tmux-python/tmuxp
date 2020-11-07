from tmuxp.plugin import TmuxpPlugin


class PluginOnWindowCreate(TmuxpPlugin):
    def __init__(self):
        self.message = '[+] This is the Tmuxp Test Plugin'

    def on_window_create(self, window):
        if window.name == 'editor':
            window.rename_window('plugin_test_owc')
        elif window.name == 'owc_mw_test':
            window.rename_window('plugin_test_owc_mw')
        elif window.name == 'owc_mw_test_2':
            window.rename_window('plugin_test_owc_mw_2')
        elif window.name == 'mp_test':
            window.rename_window('mp_test_owc')
        else:
            pass
