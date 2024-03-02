"""Tests for tmuxp shell module."""

from tmuxp import shell


def test_detect_best_shell() -> None:
    """detect_best_shell() returns a a string of the best shell."""
    result = shell.detect_best_shell()
    assert isinstance(result, str)


def test_shell_detect() -> None:
    """Tests shell detection functions."""
    assert isinstance(shell.has_bpython(), bool)
    assert isinstance(shell.has_ipython(), bool)
    assert isinstance(shell.has_ptpython(), bool)
    assert isinstance(shell.has_ptipython(), bool)
