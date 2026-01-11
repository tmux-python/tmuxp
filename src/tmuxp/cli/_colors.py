"""Backward-compatible re-exports from _internal.colors.

This module re-exports color utilities from their new location in _internal.colors
for backward compatibility with existing imports.

.. deprecated::
    Import directly from tmuxp._internal.colors instead.
"""

from __future__ import annotations

from tmuxp._internal.colors import (
    ColorMode,
    Colors,
    UnknownStyleColor,
    build_description,
    get_color_mode,
    strip_ansi,
    style,
    unstyle,
)

__all__ = [
    "ColorMode",
    "Colors",
    "UnknownStyleColor",
    "build_description",
    "get_color_mode",
    "strip_ansi",
    "style",
    "unstyle",
]
