"""Tmuxp example plugin that fails on initialization."""

import typing as t

from tmuxp.plugin import TmuxpPlugin

if t.TYPE_CHECKING:
    from tmuxp._internal.types import PluginConfigSchema


class PluginFailVersion(TmuxpPlugin):
    """A tmuxp plugin that is doomed to fail. DOOMED."""

    def __init__(self) -> None:
        config: "PluginConfigSchema" = {
            "plugin_name": "tmuxp-plugin-fail-version",
            "tmuxp_max_version": "0.0.0",
        }
        TmuxpPlugin.__init__(self, **config)
