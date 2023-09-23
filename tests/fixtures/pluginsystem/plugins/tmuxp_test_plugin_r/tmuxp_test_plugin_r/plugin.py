import typing as t

from tmuxp.plugin import TmuxpPlugin

if t.TYPE_CHECKING:
    from libtmux.session import Session


class PluginReattach(TmuxpPlugin):
    def __init__(self) -> None:
        self.message: str = "[+] This is the Tmuxp Test Plugin"

    def reattach(self, session: "Session") -> None:
        session.rename_session("plugin_test_r")
