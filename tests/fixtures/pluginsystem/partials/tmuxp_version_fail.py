"""Fixtures for tmuxp plugins for tmuxp version exceptions."""

import typing as t

from .test_plugin_helpers import MyTestTmuxpPlugin

if t.TYPE_CHECKING:
    from ._types import PluginTestConfigSchema


class TmuxpVersionFailMinPlugin(MyTestTmuxpPlugin):
    """Tmuxp plugin that fails when tmuxp below minimum version constraint."""

    def __init__(self) -> None:
        config: "PluginTestConfigSchema" = {
            "plugin_name": "tmuxp-min-version-fail",
            "tmuxp_min_version": "1.7.0",
            "tmuxp_version": "1.6.3",
        }
        MyTestTmuxpPlugin.__init__(self, **config)


class TmuxpVersionFailMaxPlugin(MyTestTmuxpPlugin):
    """Tmuxp plugin that fails when tmuxp above maximum version constraint."""

    def __init__(self) -> None:
        config: "PluginTestConfigSchema" = {
            "plugin_name": "tmuxp-max-version-fail",
            "tmuxp_max_version": "2.0.0",
            "tmuxp_version": "2.5",
        }
        MyTestTmuxpPlugin.__init__(self, **config)


class TmuxpVersionFailIncompatiblePlugin(MyTestTmuxpPlugin):
    """Tmuxp plugin that fails when tmuxp version constraint is invalid."""

    def __init__(self) -> None:
        config: "PluginTestConfigSchema" = {
            "plugin_name": "tmuxp-incompatible-version-fail",
            "tmuxp_version_incompatible": ["1.5.0"],
            "tmuxp_version": "1.5.0",
        }
        MyTestTmuxpPlugin.__init__(self, **config)
