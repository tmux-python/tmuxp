import typing as t

from tmuxp.plugin import TmuxpPlugin

if t.TYPE_CHECKING:
    from tmuxp._types import PluginConfigSchema


class PluginFailVersion(TmuxpPlugin):
    def __init__(self) -> None:
        config: "PluginConfigSchema" = {
            "plugin_name": "tmuxp-plugin-fail-version",
            "tmuxp_max_version": "0.0.0",
        }
        TmuxpPlugin.__init__(self, **config)
