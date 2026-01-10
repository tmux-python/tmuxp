"""Shared pytest fixtures for CLI tests."""

from __future__ import annotations

import pathlib

import pytest

from tmuxp.cli._colors import ColorMode, Colors


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
