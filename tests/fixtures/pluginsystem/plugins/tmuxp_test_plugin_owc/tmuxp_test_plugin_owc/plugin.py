"""Tmuxp example plugin for on_window_create."""

import typing as t

from tmuxp.plugin import TmuxpPlugin

if t.TYPE_CHECKING:
    from libtmux.window import Window


class PluginOnWindowCreate(TmuxpPlugin):
    """Tmuxp plugin to test custom functionality on window creation."""

    def __init__(self) -> None:
        self.message: str = "[+] This is the Tmuxp Test Plugin"

    def on_window_create(self, window: "Window") -> None:
        """Apply hook that runs for tmux on session reattach."""
        if window.name == "editor":
            window.rename_window("plugin_test_owc")
        elif window.name == "owc_mw_test":
            window.rename_window("plugin_test_owc_mw")
        elif window.name == "owc_mw_test_2":
            window.rename_window("plugin_test_owc_mw_2")
        elif window.name == "mp_test":
            window.rename_window("mp_test_owc")
        else:
            pass
