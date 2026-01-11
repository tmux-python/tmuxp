"""Shared pytest fixtures for _internal tests."""

from __future__ import annotations

import pytest

from tmuxp._internal.colors import ColorMode, Colors

# ANSI escape codes for test assertions
# These constants improve test readability by giving semantic names to color codes
ANSI_GREEN = "\033[32m"
ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_BLUE = "\033[34m"
ANSI_MAGENTA = "\033[35m"
ANSI_CYAN = "\033[36m"
ANSI_BRIGHT_CYAN = "\033[96m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


@pytest.fixture
def colors_always(monkeypatch: pytest.MonkeyPatch) -> Colors:
    """Colors instance with ALWAYS mode and NO_COLOR cleared."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    return Colors(ColorMode.ALWAYS)


@pytest.fixture
def colors_never() -> Colors:
    """Colors instance with colors disabled."""
    return Colors(ColorMode.NEVER)
