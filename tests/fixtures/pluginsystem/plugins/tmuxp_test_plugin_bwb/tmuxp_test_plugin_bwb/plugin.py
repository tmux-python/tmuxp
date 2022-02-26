from tmuxp.plugin import TmuxpPlugin


class PluginBeforeWorkspaceBuilder(TmuxpPlugin):
    def __init__(self):
        self.message = "[+] This is the Tmuxp Test Plugin"

    def before_workspace_builder(self, session):
        session.rename_session("plugin_test_bwb")
