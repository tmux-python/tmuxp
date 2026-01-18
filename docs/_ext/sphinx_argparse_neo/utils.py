"""Text processing utilities for sphinx_argparse_neo.

This module provides utilities for cleaning argparse output before rendering:
- strip_ansi: Remove ANSI escape codes (for when FORCE_COLOR is set)
"""

from __future__ import annotations

import re

# ANSI escape code pattern - matches CSI sequences like \033[32m, \033[1;34m, etc.
_ANSI_RE = re.compile(r"\033\[[;?0-9]*[a-zA-Z]")


def strip_ansi(text: str) -> str:
    r"""Remove ANSI escape codes from text.

    When FORCE_COLOR is set in the environment, argparse may include ANSI
    escape codes in its output. This function removes them so the output
    renders correctly in Sphinx documentation.

    Parameters
    ----------
    text : str
        Text potentially containing ANSI codes.

    Returns
    -------
    str
        Text with ANSI codes removed.

    Examples
    --------
    >>> strip_ansi("plain text")
    'plain text'
    >>> strip_ansi("\033[32mgreen\033[0m")
    'green'
    >>> strip_ansi("\033[1;34mbold blue\033[0m")
    'bold blue'
    """
    return _ANSI_RE.sub("", text)
