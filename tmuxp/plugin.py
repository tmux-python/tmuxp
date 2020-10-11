class TmuxpPluginInterface:
    def __init__(self):
        """
        Initialize plugin interface.
        """
        pass

    def before_workspace_builder(self, session):
        """
        Provide a session hook previous to creating the workspace.

        This runs after the session has been created but before any of 
        the windows/panes/commands are entered.

        Parameters
        ----------
        session : :class:`libtmux.Session`
            session to hook into
        """
        pass

    def on_window_create(self, window):
        """
        Provide a window hook previous to doing anything with a window.

        This runs runs before anything is created in the windows, like panes.

        Parameters
        ----------
        window: :class:`libtmux.Window`
            window to hook into
        """
        pass

    def after_window_finished(self, window):
        """
        Provide a window hook after creating the window.

        This runs after everything has been created in the window, including
        the panes and all of the commands for the panes. It also runs after the
        ``options_after`` has been applied to the window.

        Parameters
        ----------
        window: :class:`libtmux.Window`
            window to hook into
        """
        pass

    def before_script(self, session):
        """
        Provide a session hook after the workspace has been built.

        This runs after the workspace has been loaded with ``tmuxp load``. It
        augments instead of replaces the ``before_script`` section of the
        configuration. 

        This hook provides access to the LibTmux.session object for any 
        behavior that would be used in the ``before_script`` section of the 
        configuration file that needs access directly to the session object.
        This runs after the workspace has been loaded with ``tmuxp load``. 
        
        The hook augments, rather than replaces, the ``before_script`` section 
        of the configuration. While it is possible to do all of the 
        ``before_script`` configuration in this function, if a shell script 
        is currently being used for the configuration, it would be cleaner to 
        continue using the script in the ``before_section``.
        
        If changes to the session need to be made prior to 
        anything being built, please use ``before_workspace_builder`` instead.

        Parameters
        ----------
        session : :class:`libtmux.Session`
            session to hook into
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