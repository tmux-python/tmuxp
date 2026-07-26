"""Internal, :const:`typing.TYPE_CHECKING` guarded :term:`typings <annotation>`.

These are _not_ to be imported at runtime as `typing_extensions` is not
bundled with tmuxp. Usage example:

>>> import typing as t

>>> if t.TYPE_CHECKING:
...     from tmuxp._internal.types import PluginConfigSchema
...
"""

from __future__ import annotations

import logging
import typing as t
from typing import TypedDict

logger = logging.getLogger(__name__)

if t.TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import NotRequired
    else:
        from typing_extensions import NotRequired


class PluginConfigSchema(TypedDict):
    """Keyword arguments accepted by :class:`tmuxp.plugin.TmuxpPlugin`.

    Every key is optional. :func:`tmuxp.plugin.setup_plugin_config` fills each
    omitted key from ``tmuxp.plugin.DEFAULT_CONFIG`` before the plugin runs its
    version checks.

    Attributes
    ----------
    plugin_name : NotRequired[str]
        Name of the plugin, used to identify it in version incompatibility
        messages.
    tmux_min_version : NotRequired[str]
        Oldest tmux version the plugin supports.
    tmux_max_version : NotRequired[str]
        Newest tmux version the plugin supports.
    tmux_version_incompatible : NotRequired[list[str]]
        Individual tmux versions the plugin rejects even though they fall
        inside the min / max range.
    libtmux_min_version : NotRequired[str]
        Oldest libtmux version the plugin supports.
    libtmux_max_version : NotRequired[str]
        Newest libtmux version the plugin supports.
    libtmux_version_incompatible : NotRequired[list[str]]
        Individual libtmux versions the plugin rejects even though they fall
        inside the min / max range.
    tmuxp_min_version : NotRequired[str]
        Oldest tmuxp version the plugin supports.
    tmuxp_max_version : NotRequired[str]
        Newest tmuxp version the plugin supports.
    tmuxp_version_incompatible : NotRequired[list[str]]
        Individual tmuxp versions the plugin rejects even though they fall
        inside the min / max range.
    """

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
