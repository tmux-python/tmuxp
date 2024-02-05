"""Tests for tmuxp's tmux(1) hooks."""
import typing as t

from tmuxp.cli.load import set_layout_hook

if t.TYPE_CHECKING:
    from libtmux.session import Session


def test_set_layout_hook(session: "Session") -> None:
    """Test set_layout_hook."""
    set_layout_hook(session, "main-vertical")
