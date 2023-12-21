"""Tmuxp example plugin for after_window_finished."""
import typing as t

from tmuxp.plugin import TmuxpPlugin

if t.TYPE_CHECKING:
    from libtmux.window import Window


class PluginAfterWindowFinished(TmuxpPlugin):
    """Tmuxp plugin that runs after window creation completes."""

    def __init__(self) -> None:
        self.message: str = "[+] This is the Tmuxp Test Plugin"

    def after_window_finished(self, window: "Window") -> None:
        """Run hook after window creation completed."""
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
