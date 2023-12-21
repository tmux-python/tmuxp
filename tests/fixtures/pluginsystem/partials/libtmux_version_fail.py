"""Fixtures for tmuxp plugins for libtmux version exceptions."""
import typing as t

from .test_plugin_helpers import MyTestTmuxpPlugin

if t.TYPE_CHECKING:
    from ._types import PluginTestConfigSchema


class LibtmuxVersionFailMinPlugin(MyTestTmuxpPlugin):
    """Tmuxp plugin that fails when libtmux below minimum version constraint."""

    def __init__(self) -> None:
        config: "PluginTestConfigSchema" = {
            "plugin_name": "libtmux-min-version-fail",
            "libtmux_min_version": "0.8.3",
            "libtmux_version": "0.7.0",
        }
        MyTestTmuxpPlugin.__init__(self, **config)


class LibtmuxVersionFailMaxPlugin(MyTestTmuxpPlugin):
    """Tmuxp plugin that fails when libtmux above maximum version constraint."""

    def __init__(self) -> None:
        config: "PluginTestConfigSchema" = {
            "plugin_name": "libtmux-max-version-fail",
            "libtmux_max_version": "3.0",
            "libtmux_version": "3.5",
        }
        MyTestTmuxpPlugin.__init__(self, **config)


class LibtmuxVersionFailIncompatiblePlugin(MyTestTmuxpPlugin):
    """Tmuxp plugin that fails when libtmux version constraint is invalid."""

    def __init__(self) -> None:
        config: "PluginTestConfigSchema" = {
            "plugin_name": "libtmux-incompatible-version-fail",
            "libtmux_version_incompatible": ["0.7.1"],
            "libtmux_version": "0.7.1",
        }
        MyTestTmuxpPlugin.__init__(self, **config)
