"""Fixtures and configuration for docs extension tests."""

from __future__ import annotations

import pathlib
import sys

# Add docs/_ext to path so we can import the extension module
docs_ext_path = pathlib.Path(__file__).parent.parent.parent.parent / "docs" / "_ext"
if str(docs_ext_path) not in sys.path:
    sys.path.insert(0, str(docs_ext_path))
