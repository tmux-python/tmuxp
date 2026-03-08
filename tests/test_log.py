"""Tests for tmuxp.log module."""

from __future__ import annotations

import logging
import sys

import pytest

from tmuxp.log import (
    LEVEL_COLORS,
    DebugLogFormatter,
    LogFormatter,
    tmuxp_echo,
)


def test_level_colors_no_colorama() -> None:
    """LEVEL_COLORS must be raw ANSI escape strings, not colorama objects."""
    for level, code in LEVEL_COLORS.items():
        assert code.startswith("\033["), (
            f"LEVEL_COLORS[{level!r}] should start with ANSI ESC, got {code!r}"
        )


def test_log_formatter_format_plain_text() -> None:
    """LogFormatter.format() produces plain text without ANSI when unstylized."""
    formatter = LogFormatter()
    record = logging.LogRecord(
        name="tmuxp",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test message",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "test message" in output
    assert "\033[" not in output


def test_debug_log_formatter_format_smoke() -> None:
    """DebugLogFormatter.format() runs without error."""
    formatter = DebugLogFormatter()
    record = logging.LogRecord(
        name="tmuxp",
        level=logging.DEBUG,
        pathname="",
        lineno=42,
        msg="debug message",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "debug message" in output


def test_timestamp_format_has_minutes() -> None:
    """Timestamp format must use %M (minutes), not %m (month)."""
    formatter = LogFormatter()
    record = logging.LogRecord(
        name="tmuxp",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="ts check",
        args=(),
        exc_info=None,
    )
    formatter.format(record)
    # asctime is set during format(); if %m were used, seconds portion would
    # show month (01-12) instead of minutes (00-59) — we can't easily
    # distinguish that directly, so just verify the format string constant.
    # Inspect the source: date_format in LogFormatter.format is "%H:%M:%S"
    import inspect

    import tmuxp.log as log_module

    src = inspect.getsource(log_module.LogFormatter.format)
    assert '"%H:%M:%S"' in src, "Timestamp format must be %H:%M:%S (M = minutes)"


def test_tmuxp_echo_default_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """tmuxp_echo writes to stdout by default."""
    tmuxp_echo("hello stdout")
    captured = capsys.readouterr()
    assert captured.out == "hello stdout\n"
    assert captured.err == ""


def test_tmuxp_echo_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    """tmuxp_echo writes to stderr when file=sys.stderr."""
    tmuxp_echo("hello stderr", file=sys.stderr)
    captured = capsys.readouterr()
    assert captured.err == "hello stderr\n"
    assert captured.out == ""


def test_tmuxp_echo_none_is_no_op(capsys: pytest.CaptureFixture[str]) -> None:
    """tmuxp_echo(None) produces no output."""
    tmuxp_echo(None)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
