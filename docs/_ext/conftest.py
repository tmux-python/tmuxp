"""Pytest configuration for docs/_ext doctests.

This module sets up sys.path so that sphinx_argparse_neo and other extension
modules can be imported correctly during pytest doctest collection.
"""

from __future__ import annotations

import pathlib
import sys

# Add docs/_ext to sys.path so sphinx_argparse_neo can import itself
_ext_dir = pathlib.Path(__file__).parent
if str(_ext_dir) not in sys.path:
    sys.path.insert(0, str(_ext_dir))
