"""Shared pytest fixtures for CLI tests."""

from __future__ import annotations

import pathlib

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


@pytest.fixture
def mock_home(monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Mock home directory for privacy tests.

    Sets pathlib.Path.home() to return /home/testuser.
    """
    home = pathlib.Path("/home/testuser")
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)
    return home


@pytest.fixture
def isolated_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> pathlib.Path:
    """Isolate test from user's home directory and environment.

    Sets up tmp_path as HOME with XDG_CONFIG_HOME, clears TMUXP_CONFIGDIR
    and NO_COLOR, and changes the working directory to tmp_path.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
    monkeypatch.delenv("TMUXP_CONFIGDIR", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
    return tmp_path
