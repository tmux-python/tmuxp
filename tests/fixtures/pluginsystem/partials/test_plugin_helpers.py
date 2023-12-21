"""Tmuxp test plugin for asserting version constraints."""
import typing as t

from tmuxp.plugin import TmuxpPlugin

if t.TYPE_CHECKING:
    from typing_extensions import Unpack

    from tmuxp._internal.types import PluginConfigSchema

    from ._types import PluginTestConfigSchema


class MyTestTmuxpPlugin(TmuxpPlugin):
    """Base class for testing tmuxp plugins with version constraints."""

    def __init__(self, **config: "Unpack[PluginTestConfigSchema]") -> None:
        assert isinstance(config, dict)
        tmux_version = config.pop("tmux_version", None)
        libtmux_version = config.pop("libtmux_version", None)
        tmuxp_version = config.pop("tmuxp_version", None)

        t.cast("PluginConfigSchema", config)

        assert "tmux_version" not in config

        # tests/fixtures/pluginsystem/partials/test_plugin_helpers.py:24: error: Extra
        # argument "tmux_version" from **args for "__init__" of "TmuxpPlugin"  [misc]
        super().__init__(**config)  # type:ignore

        # WARNING! This should not be done in anything but a test
        if tmux_version:
            self.version_constraints["tmux"]["version"] = tmux_version
        if libtmux_version:
            self.version_constraints["libtmux"]["version"] = libtmux_version
        if tmuxp_version:
            self.version_constraints["tmuxp"]["version"] = tmuxp_version

        self._version_check()
