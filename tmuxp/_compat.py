# -*- coding: utf8 -*-
# flake8: NOQA
import sys

PY3 = sys.version_info[0] == 3
PYMINOR = sys.version_info[1]
PYPATCH = sys.version_info[2]

_identity = lambda x: x

if PY3 and PYMINOR >= 7:
    breakpoint = breakpoint
else:
    import pdb

    breakpoint = pdb.set_trace


console_encoding = sys.__stdout__.encoding

implements_to_string = _identity


def console_to_str(s):
    """From pypa/pip project, pip.backwardwardcompat. License MIT."""
    try:
        return s.decode(console_encoding)
    except UnicodeDecodeError:
        return s.decode('utf_8')
