"""Tests for workspace builder options (:mod:`tmuxp.workspace.options`)."""

from __future__ import annotations

import typing as t

import pytest

from tmuxp.workspace.options import (
    PaneReadiness,
    WorkspaceBuilderOptions,
    resolve_session_shell,
    shell_is_zsh,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, PaneReadiness.AUTO),
        ("auto", PaneReadiness.AUTO),
        ("AUTO", PaneReadiness.AUTO),
        (True, PaneReadiness.ALWAYS),
        ("always", PaneReadiness.ALWAYS),
        ("on", PaneReadiness.ALWAYS),
        ("yes", PaneReadiness.ALWAYS),
        ("1", PaneReadiness.ALWAYS),
        (1, PaneReadiness.ALWAYS),
        (False, PaneReadiness.NEVER),
        ("never", PaneReadiness.NEVER),
        ("off", PaneReadiness.NEVER),
        ("no", PaneReadiness.NEVER),
        ("0", PaneReadiness.NEVER),
        (0, PaneReadiness.NEVER),
        (PaneReadiness.ALWAYS, PaneReadiness.ALWAYS),
    ],
)
def test_pane_readiness_from_config(value: t.Any, expected: PaneReadiness) -> None:
    """from_config maps canonical values and truthy/falsy aliases."""
    assert PaneReadiness.from_config(value) is expected


@pytest.mark.parametrize("value", ["sometimes", "maybe", "2", ""])
def test_pane_readiness_from_config_invalid(value: str) -> None:
    """from_config rejects unknown values with an actionable error."""
    with pytest.raises(ValueError, match="pane_readiness"):
        PaneReadiness.from_config(value)


def test_workspace_builder_options_defaults() -> None:
    """An absent catalog yields AUTO readiness."""
    assert WorkspaceBuilderOptions.from_config({}).pane_readiness is PaneReadiness.AUTO
    cfg = {"session_name": "x", "windows": []}
    assert WorkspaceBuilderOptions.from_config(cfg).pane_readiness is PaneReadiness.AUTO


def test_workspace_builder_options_reads_catalog() -> None:
    """from_config reads pane_readiness from the catalog."""
    cfg = {"workspace_builder_options": {"pane_readiness": "never"}}
    options = WorkspaceBuilderOptions.from_config(cfg)
    assert options.pane_readiness is PaneReadiness.NEVER


def test_workspace_builder_options_invalid_catalog_type() -> None:
    """A non-mapping catalog is rejected."""
    with pytest.raises(TypeError, match="must be a mapping"):
        WorkspaceBuilderOptions.from_config({"workspace_builder_options": ["nope"]})


@pytest.mark.parametrize(
    ("shell", "expected"),
    [
        ("/usr/bin/zsh", True),
        ("/bin/zsh", True),
        ("zsh", True),
        ("/bin/bash", False),
        ("/bin/sh", False),
        ("", False),
        (None, False),
    ],
)
def test_shell_is_zsh(shell: str | None, expected: bool) -> None:
    """shell_is_zsh detects zsh by name."""
    assert shell_is_zsh(shell) is expected


class _FakeSession:
    """Minimal stand-in exposing ``show_option`` for shell resolution."""

    def __init__(self, shell: str | None) -> None:
        self._shell = shell

    def show_option(self, name: str, **kwargs: t.Any) -> str | None:
        """Return the canned default-shell value."""
        return self._shell


def test_resolve_session_shell_prefers_default_shell() -> None:
    """The tmux default-shell wins over $SHELL."""
    shell = resolve_session_shell(
        _FakeSession("/usr/bin/zsh"),
        env={"SHELL": "/bin/bash"},
    )
    assert shell == "/usr/bin/zsh"


def test_resolve_session_shell_falls_back_to_env() -> None:
    """$SHELL is the fallback when default-shell is empty."""
    shell = resolve_session_shell(_FakeSession(None), env={"SHELL": "/bin/bash"})
    assert shell == "/bin/bash"


def test_resolve_session_shell_empty_when_unknown() -> None:
    """Returns an empty string when neither source resolves."""
    assert resolve_session_shell(_FakeSession(None), env={}) == ""
