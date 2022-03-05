from distutils.version import LooseVersion

import libtmux
from libtmux.common import get_version

from .__about__ import __version__
from .exc import TmuxpPluginException

#: Minimum version of tmux required to run libtmux
TMUX_MIN_VERSION = "1.8"

#: Most recent version of tmux supported
TMUX_MAX_VERSION = None

#: Minimum version of libtmux required to run libtmux
LIBTMUX_MIN_VERSION = "0.8.3"

#: Most recent version of libtmux supported
LIBTMUX_MAX_VERSION = None

#: Minimum version of tmuxp required to use plugins
TMUXP_MIN_VERSION = "1.6.0"

#: Most recent version of tmuxp
TMUXP_MAX_VERSION = None


class TmuxpPlugin:
    def __init__(
        self,
        plugin_name="tmuxp-plugin",
        tmux_min_version=TMUX_MIN_VERSION,
        tmux_max_version=TMUX_MAX_VERSION,
        tmux_version_incompatible=None,
        libtmux_min_version=LIBTMUX_MIN_VERSION,
        libtmux_max_version=LIBTMUX_MAX_VERSION,
        libtmux_version_incompatible=None,
        tmuxp_min_version=TMUXP_MIN_VERSION,
        tmuxp_max_version=TMUXP_MAX_VERSION,
        tmuxp_version_incompatible=None,
    ):
        """
        Initialize plugin.

        The default version values are set to the versions that the plugin
        system requires.

        Parameters
        ----------
        plugin_name : str
            Name of the child plugin. Used in error message plugin fails to
            load

        tmux_min_version : str
            Min version of tmux that the plugin supports

        tmux_max_version : str
            Min version of tmux that the plugin supports

        tmux_version_incompatible : list
            Versions of tmux that are incompatible with the plugin

        libtmux_min_version : str
            Min version of libtmux that the plugin supports

        libtmux_max_version : str
            Max version of libtmux that the plugin supports

        libtmux_version_incompatible : list
            Versions of libtmux that are incompatible with the plugin

        tmuxp_min_version : str
            Min version of tmuxp that the plugin supports

        tmuxp_max_version : str
            Max version of tmuxp that the plugin supports

        tmuxp_version_incompatible : list
            Versions of tmuxp that are incompatible with the plugin

        """
        self.plugin_name = plugin_name

        # Dependency versions
        self.tmux_version = get_version()
        self.libtmux_version = libtmux.__version__
        self.tmuxp_version = LooseVersion(__version__)

        self.version_constraints = {
            "tmux": {
                "version": self.tmux_version,
                "vmin": tmux_min_version,
                "vmax": tmux_max_version,
                "incompatible": tmux_version_incompatible
                if tmux_version_incompatible
                else [],
            },
            "libtmux": {
                "version": self.libtmux_version,
                "vmin": libtmux_min_version,
                "vmax": libtmux_max_version,
                "incompatible": libtmux_version_incompatible
                if libtmux_version_incompatible
                else [],
            },
            "tmuxp": {
                "version": self.tmuxp_version,
                "vmin": tmuxp_min_version,
                "vmax": tmuxp_max_version,
                "incompatible": tmuxp_version_incompatible
                if tmuxp_version_incompatible
                else [],
            },
        }

        self._version_check()

    def _version_check(self):
        """
        Check all dependency versions for compatibility.
        """
        for dep, constraints in self.version_constraints.items():
            try:
                assert self._pass_version_check(**constraints)
            except AssertionError:
                raise TmuxpPluginException(
                    "Incompatible {dep} version: {version}\n{plugin_name} "
                    "requirements:\nmin: {vmin} | max: {vmax} | "
                    "incompatible: {incompatible}\n".format(
                        dep=dep, plugin_name=self.plugin_name, **constraints
                    )
                )

    def _pass_version_check(self, version, vmin, vmax, incompatible):
        """
        Provide affirmative if version compatibility is correct.
        """
        if vmin and version < LooseVersion(vmin):
            return False
        if vmax and version > LooseVersion(vmax):
            return False
        if version in incompatible:
            return False

        return True

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

    def on_window_create(self, window):
        """
        Provide a window hook previous to doing anything with a window.

        This runs runs before anything is created in the windows, like panes.

        Parameters
        ----------
        window: :class:`libtmux.Window`
            window to hook into
        """

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

    def reattach(self, session):
        """
        Provide a session hook before reattaching to the session.

        Parameters
        ----------
        session : :class:`libtmux.Session`
            session to hook into
        """
