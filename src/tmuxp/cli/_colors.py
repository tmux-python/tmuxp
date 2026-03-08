"""Backward-compatible re-exports from _internal.colors.

This module re-exports color utilities from their new location in _internal.colors
for backward compatibility with existing imports.

.. deprecated::
    Import directly from tmuxp._internal.colors instead.
"""

from __future__ import annotations

import logging

from tmuxp._internal.colors import (
    ANSI_SEQ_RE,
    ColorMode,
    Colors,
    UnknownStyleColor,
    build_description,
    get_color_mode,
    strip_ansi,
    style,
    unstyle,
)

logger = logging.getLogger(__name__)

__all__ = [
    "ANSI_SEQ_RE",
    "ColorMode",
    "Colors",
    "UnknownStyleColor",
    "build_description",
    "get_color_mode",
    "strip_ansi",
    "style",
    "unstyle",
]
