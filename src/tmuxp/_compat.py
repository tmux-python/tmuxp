from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)

PY3 = sys.version_info[0] == 3
PYMINOR = sys.version_info[1]
PYPATCH = sys.version_info[2]


def _identity(x: object) -> object:
    """Return *x* unchanged — used as a no-op decorator.

    Examples
    --------
    >>> from tmuxp._compat import _identity

    Strings pass through unchanged:

    >>> _identity("hello")
    'hello'

    Integers pass through unchanged:

    >>> _identity(42)
    42
    """
    return x


if PY3 and PYMINOR >= 7:
    breakpoint = breakpoint  # noqa: A001
else:
    import pdb

    breakpoint = pdb.set_trace  # noqa: A001


implements_to_string = _identity
