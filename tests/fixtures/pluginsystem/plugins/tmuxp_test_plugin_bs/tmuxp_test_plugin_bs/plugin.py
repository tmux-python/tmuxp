"""Tmux plugin that runs before_script, if it is declared in configuration."""
import typing as t

from tmuxp.plugin import TmuxpPlugin

if t.TYPE_CHECKING:
    from libtmux.session import Session


class PluginBeforeScript(TmuxpPlugin):
    """Tmuxp plugin that runs before_script."""

    def __init__(self) -> None:
        self.message: str = "[+] This is the Tmuxp Test Plugin"

    def before_script(self, session: "Session") -> None:
        """Run hook during before_script, if it is declared."""
        session.rename_session("plugin_test_bs")
