"""Internal, :const:`typing.TYPE_CHECKING` scoped :term:`type annotations <annotation>`.

These are _not_ to be imported at runtime as `typing_extensions` is not
bundled with tmuxp. Usage example:

>>> import typing as t

>>> if t.TYPE_CHECKING:
...     from tmuxp.fixtures.pluginsystem.partials._types import PluginConfigSchema
...
"""

from __future__ import annotations

from typing_extensions import NotRequired, TypedDict


class PluginTestConfigSchema(TypedDict):
    """Same as PluginConfigSchema, but with tmux, libtmux, and tmuxp version."""

    tmux_version: NotRequired[str]
    libtmux_version: NotRequired[str]
    tmuxp_version: NotRequired[str]

    # Normal keys
    plugin_name: NotRequired[str]
    tmux_min_version: NotRequired[str]
    tmux_max_version: NotRequired[str]
    tmux_version_incompatible: NotRequired[list[str]]
    libtmux_min_version: NotRequired[str]
    libtmux_max_version: NotRequired[str]
    libtmux_version_incompatible: NotRequired[list[str]]
    tmuxp_min_version: NotRequired[str]
    tmuxp_max_version: NotRequired[str]
    tmuxp_version_incompatible: NotRequired[list[str]]
