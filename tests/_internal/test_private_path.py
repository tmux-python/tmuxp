"""Tests for PrivatePath privacy-masking utilities."""

from __future__ import annotations

import pathlib

import pytest

from tmuxp._internal.private_path import PrivatePath, collapse_home_in_string

# PrivatePath tests


def test_private_path_collapses_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """PrivatePath replaces home directory with ~."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    path = PrivatePath("/home/testuser/projects/tmuxp")
    assert str(path) == "~/projects/tmuxp"


def test_private_path_collapses_home_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    """PrivatePath handles exact home directory match."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    path = PrivatePath("/home/testuser")
    assert str(path) == "~"


def test_private_path_preserves_non_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """PrivatePath preserves paths outside home directory."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    path = PrivatePath("/usr/bin/tmux")
    assert str(path) == "/usr/bin/tmux"


def test_private_path_preserves_tmp(monkeypatch: pytest.MonkeyPatch) -> None:
    """PrivatePath preserves /tmp paths."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    path = PrivatePath("/tmp/example")
    assert str(path) == "/tmp/example"


def test_private_path_preserves_already_collapsed() -> None:
    """PrivatePath preserves paths already starting with ~."""
    path = PrivatePath("~/already/collapsed")
    assert str(path) == "~/already/collapsed"


def test_private_path_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    """PrivatePath repr shows class name and collapsed path."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    path = PrivatePath("/home/testuser/config.yaml")
    assert repr(path) == "PrivatePath('~/config.yaml')"


def test_private_path_in_fstring(monkeypatch: pytest.MonkeyPatch) -> None:
    """PrivatePath works in f-strings with collapsed home."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    path = PrivatePath("/home/testuser/.tmuxp/session.yaml")
    result = f"config: {path}"
    assert result == "config: ~/.tmuxp/session.yaml"


def test_private_path_similar_prefix_not_collapsed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PrivatePath does not collapse paths with similar prefix but different user."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    # /home/testuser2 should NOT be collapsed even though it starts with /home/testuser
    path = PrivatePath("/home/testuser2/projects")
    assert str(path) == "/home/testuser2/projects"


# collapse_home_in_string tests


def test_collapse_home_in_string_single_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """collapse_home_in_string handles a single path."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    result = collapse_home_in_string("/home/testuser/.local/bin")
    assert result == "~/.local/bin"


def test_collapse_home_in_string_multiple_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """collapse_home_in_string handles colon-separated paths."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    result = collapse_home_in_string(
        "/home/testuser/bin:/home/testuser/.cargo/bin:/usr/bin"
    )
    assert result == "~/bin:~/.cargo/bin:/usr/bin"


def test_collapse_home_in_string_no_home_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """collapse_home_in_string preserves paths not under home."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    result = collapse_home_in_string("/usr/bin:/bin:/usr/local/bin")
    assert result == "/usr/bin:/bin:/usr/local/bin"


def test_collapse_home_in_string_mixed_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """collapse_home_in_string handles mixed home and non-home paths."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path("/home/testuser"))

    result = collapse_home_in_string("/usr/bin:/home/testuser/.local/bin:/bin")
    assert result == "/usr/bin:~/.local/bin:/bin"


def test_collapse_home_in_string_empty() -> None:
    """collapse_home_in_string handles empty string."""
    result = collapse_home_in_string("")
    assert result == ""
