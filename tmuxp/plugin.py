class TmuxpPluginInterface:
    def __init__(self):
        """
        Initialize plugin interface.
        """
        pass

    def before_workspace_builder(self, session):
        """
        Provide a session hook previous to creating the workspace.

        Parameters
        ----------
        session : :class:`libtmux.Session`
            session to hook into

        Notes
        -----
        This runs after the session has been created but before any of 
        the windows/panes/commands are entered.
        """
        pass

    def on_window_create(self, window):
        """
        Provide a window hook previous to creating the window.

        Parameters
        ----------
        window: :class:`libtmux.Window`
            window to hook into
        
        Notes
        -----
        This runs runs before anything is created in the windows, like panes.
        """
        pass

    def after_window_finished(self, window):
        """
        Provide a window hook after creating the window.

        Parameters
        ----------
        window: :class:`libtmux.Window`
            window to hook into

        Notes
        -----
        This runs after everything has been created in the window, including
        the paes and all of the commands for the panes. It also runs after the
        ``options_after`` have been applied to the window.
        """
        pass

    def before_script(self, session):
        """
        Provide a session hook after the workspace has been built.

        Parameters
        ----------
        session : :class:`libtmux.Session`
            session to hook into

        Notes
        -----
        This runs after the workspace has been loaded with ``tmuxp load``. It
        augments instead of replaces the ``before_script`` section of the
        configuration. If changes to the session need to be made prior to 
        anything being built, please use ``before_workspace_builder`` instead.
        """
        pass

    def reattach(self, session):
        """
        Provide a session hook before reattaching to the session.

        Parameters
        ----------
        session : :class:`libtmux.Session`
            session to hook into
        """
        pass