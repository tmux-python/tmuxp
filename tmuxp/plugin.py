class TmuxpPluginInterface:
    def __init__(self):
        pass

    def before_workspace_builder(self, session):
        pass

    def before_script(self, session):
        pass

    def reattach(self, session):
        pass

    def on_window_create(self, window):
        pass

    def after_window_finished(self, window):  
        pass