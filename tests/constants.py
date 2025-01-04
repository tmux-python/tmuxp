"""Constant variables for tmuxp tests."""

from __future__ import annotations

import pathlib

TESTS_PATH = pathlib.Path(__file__).parent
EXAMPLE_PATH = TESTS_PATH.parent / "examples"
FIXTURE_PATH = TESTS_PATH / "fixtures"
