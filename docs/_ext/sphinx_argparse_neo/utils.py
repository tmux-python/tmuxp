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


# RST emphasis pattern: matches -* that would trigger inline emphasis errors.
# Pattern matches: non-whitespace/non-backslash char, followed by -*, NOT followed by
# another * (which would be strong emphasis **).
_RST_EMPHASIS_RE = re.compile(r"(?<=[^\s\\])-\*(?!\*)")


def escape_rst_emphasis(text: str) -> str:
    r"""Escape asterisks that would trigger RST inline emphasis.

    RST interprets ``*text*`` as emphasis. When argparse help text contains
    glob patterns like ``django-*``, the ``-*`` sequence triggers RST
    "Inline emphasis start-string without end-string" warnings.

    This function escapes such asterisks to prevent RST parsing errors.

    Parameters
    ----------
    text : str
        Text potentially containing problematic asterisks.

    Returns
    -------
    str
        Text with asterisks escaped where needed.

    Examples
    --------
    >>> escape_rst_emphasis('tmuxp load "my-*"')
    'tmuxp load "my-\\*"'
    >>> escape_rst_emphasis("plain text")
    'plain text'
    >>> escape_rst_emphasis("*emphasis* is ok")
    '*emphasis* is ok'
    """
    return _RST_EMPHASIS_RE.sub(r"-\*", text)
