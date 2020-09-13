from tmuxp.plugin import TmuxpPluginInterface

class PluginBeforeWorkspaceBuilder(TmuxpPluginInterface):
    def __init__(self):
        self.message = f'[+] This is the Tmuxp Test Plugin'

    def before_workspace_builder(self, session):
        session.rename_session('plugin_test_bwb')

