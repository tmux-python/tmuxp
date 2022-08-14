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

    breakpoint = pdb.set_trace  # type: ignore


console_encoding = sys.__stdout__.encoding

implements_to_string = _identity
