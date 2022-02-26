from tmuxp.plugin import TmuxpPlugin


class PluginAfterWindowFinished(TmuxpPlugin):
    def __init__(self):
        self.message = "[+] This is the Tmuxp Test Plugin"

    def after_window_finished(self, window):
        if window.name == "editor":
            window.rename_window("plugin_test_awf")
        elif window.name == "awf_mw_test":
            window.rename_window("plugin_test_awf_mw")
        elif window.name == "awf_mw_test_2":
            window.rename_window("plugin_test_awf_mw_2")
        elif window.name == "mp_test_owc":
            window.rename_window("mp_test_awf")
        else:
            pass
