class TestPluginOne:
    def __init__(self):
        self.message = f'[+] This is the Tmuxp Test Plugin'

    def before_workspace_builder(self, session):
        pass

    def before_script(self, session):
        pass

    def reattach(self, session):
        pass

    def on_window_create(self, window):
        if window.name == 'editor': 
            pass

    def after_window_finished(self, window):  
        pass