"""Internal, :const:`typing.TYPE_CHECKING` guarded :term:`typings <annotation>`.

These are _not_ to be imported at runtime as `typing_extensions` is not
bundled with tmuxp. Usage example:

>>> import typing as t

>>> if t.TYPE_CHECKING:
...     from tmuxp._internal.types import PluginConfigSchema
...
"""

from __future__ import annotations

import typing as t
from typing import TypedDict

if t.TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import NotRequired
    else:
        from typing_extensions import NotRequired


class PluginConfigSchema(TypedDict):
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


class ShellCommandConfig(TypedDict):
    """Shell command configuration."""

    cmd: str
    enter: NotRequired[bool]
    suppress_history: NotRequired[bool]


ShellCommandValue = t.Union[
    str, ShellCommandConfig, list[t.Union[str, ShellCommandConfig]]
]


class PaneConfig(TypedDict, total=False):
    """Pane configuration."""

    shell_command: NotRequired[ShellCommandValue]
    shell_command_before: NotRequired[ShellCommandValue]
    start_directory: NotRequired[str]
    environment: NotRequired[dict[str, str]]
    focus: NotRequired[str | bool]
    suppress_history: NotRequired[bool]
    target: NotRequired[str]


PaneValue = t.Union[str, PaneConfig, None]


class WindowConfig(TypedDict, total=False):
    """Window configuration."""

    window_name: str
    start_directory: NotRequired[str]
    shell_command_before: NotRequired[ShellCommandValue]
    shell_command_after: NotRequired[ShellCommandValue]
    layout: NotRequired[str]
    clear: NotRequired[bool]
    options: NotRequired[dict[str, t.Any]]
    options_after: NotRequired[dict[str, t.Any]]
    environment: NotRequired[dict[str, str]]
    focus: NotRequired[str | bool]
    suppress_history: NotRequired[bool]
    panes: NotRequired[list[PaneValue]]


class WorkspaceConfig(TypedDict, total=False):
    """Complete tmuxp workspace configuration."""

    session_name: str | None  # Can be None during import
    start_directory: NotRequired[str]
    before_script: NotRequired[str]
    shell_command_before: NotRequired[ShellCommandValue]
    shell_command: NotRequired[ShellCommandValue]  # Used in import
    environment: NotRequired[dict[str, str]]
    global_options: NotRequired[dict[str, t.Any]]
    options: NotRequired[dict[str, t.Any]]
    config: NotRequired[str]  # tmux config file path
    socket_name: NotRequired[str]  # tmux socket name
    plugins: NotRequired[list[str | PluginConfigSchema]]
    suppress_history: NotRequired[bool]
    windows: list[WindowConfig]
