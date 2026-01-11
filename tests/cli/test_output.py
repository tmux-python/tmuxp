"""Tests for output formatting utilities."""

from __future__ import annotations

import io
import json
import sys

import pytest

from tmuxp.cli._output import OutputFormatter, OutputMode, get_output_mode


def test_output_mode_values() -> None:
    """Verify OutputMode enum values."""
    assert OutputMode.HUMAN.value == "human"
    assert OutputMode.JSON.value == "json"
    assert OutputMode.NDJSON.value == "ndjson"


def test_output_mode_members() -> None:
    """Verify all expected members exist."""
    members = list(OutputMode)
    assert len(members) == 3
    assert OutputMode.HUMAN in members
    assert OutputMode.JSON in members
    assert OutputMode.NDJSON in members


def test_get_output_mode_default_is_human() -> None:
    """Default mode should be HUMAN when no flags."""
    assert get_output_mode(json_flag=False, ndjson_flag=False) == OutputMode.HUMAN


def test_get_output_mode_json_flag() -> None:
    """JSON flag should return JSON mode."""
    assert get_output_mode(json_flag=True, ndjson_flag=False) == OutputMode.JSON


def test_get_output_mode_ndjson_flag() -> None:
    """NDJSON flag should return NDJSON mode."""
    assert get_output_mode(json_flag=False, ndjson_flag=True) == OutputMode.NDJSON


def test_get_output_mode_ndjson_takes_precedence() -> None:
    """NDJSON should take precedence when both flags set."""
    assert get_output_mode(json_flag=True, ndjson_flag=True) == OutputMode.NDJSON


def test_output_formatter_default_mode_is_human() -> None:
    """Default mode should be HUMAN."""
    formatter = OutputFormatter()
    assert formatter.mode == OutputMode.HUMAN


def test_output_formatter_explicit_mode() -> None:
    """Mode can be set explicitly."""
    formatter = OutputFormatter(OutputMode.JSON)
    assert formatter.mode == OutputMode.JSON


def test_output_formatter_json_buffer_initially_empty() -> None:
    """JSON buffer should start empty."""
    formatter = OutputFormatter(OutputMode.JSON)
    assert formatter._json_buffer == []


def test_emit_json_buffers_data() -> None:
    """JSON mode should buffer data."""
    formatter = OutputFormatter(OutputMode.JSON)
    formatter.emit({"name": "test1"})
    formatter.emit({"name": "test2"})
    assert len(formatter._json_buffer) == 2
    assert formatter._json_buffer[0] == {"name": "test1"}
    assert formatter._json_buffer[1] == {"name": "test2"}


def test_emit_human_does_nothing() -> None:
    """HUMAN mode emit should not buffer or output."""
    formatter = OutputFormatter(OutputMode.HUMAN)
    formatter.emit({"name": "test"})
    assert formatter._json_buffer == []


def test_emit_ndjson_writes_immediately(capsys: pytest.CaptureFixture[str]) -> None:
    """NDJSON mode should write one JSON object per line immediately."""
    formatter = OutputFormatter(OutputMode.NDJSON)
    formatter.emit({"name": "test1", "value": 42})
    formatter.emit({"name": "test2", "value": 43})

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"name": "test1", "value": 42}
    assert json.loads(lines[1]) == {"name": "test2", "value": 43}


def test_emit_text_human_outputs(capsys: pytest.CaptureFixture[str]) -> None:
    """HUMAN mode should output text."""
    formatter = OutputFormatter(OutputMode.HUMAN)
    formatter.emit_text("Hello, world!")

    captured = capsys.readouterr()
    assert captured.out == "Hello, world!\n"


def test_emit_text_json_silent(capsys: pytest.CaptureFixture[str]) -> None:
    """JSON mode should not output text."""
    formatter = OutputFormatter(OutputMode.JSON)
    formatter.emit_text("Hello, world!")

    captured = capsys.readouterr()
    assert captured.out == ""


def test_emit_text_ndjson_silent(capsys: pytest.CaptureFixture[str]) -> None:
    """NDJSON mode should not output text."""
    formatter = OutputFormatter(OutputMode.NDJSON)
    formatter.emit_text("Hello, world!")

    captured = capsys.readouterr()
    assert captured.out == ""


def test_finalize_json_outputs_array(capsys: pytest.CaptureFixture[str]) -> None:
    """JSON mode finalize should output formatted array."""
    formatter = OutputFormatter(OutputMode.JSON)
    formatter.emit({"name": "test1"})
    formatter.emit({"name": "test2"})
    formatter.finalize()

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0] == {"name": "test1"}
    assert data[1] == {"name": "test2"}


def test_finalize_json_clears_buffer() -> None:
    """JSON mode finalize should clear the buffer."""
    formatter = OutputFormatter(OutputMode.JSON)
    formatter.emit({"name": "test"})
    assert len(formatter._json_buffer) == 1

    # Capture output to prevent test pollution
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        formatter.finalize()
    finally:
        sys.stdout = old_stdout

    assert formatter._json_buffer == []


def test_finalize_json_empty_buffer_no_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON mode finalize with empty buffer should not output."""
    formatter = OutputFormatter(OutputMode.JSON)
    formatter.finalize()

    captured = capsys.readouterr()
    assert captured.out == ""


def test_finalize_human_no_op(capsys: pytest.CaptureFixture[str]) -> None:
    """HUMAN mode finalize should do nothing."""
    formatter = OutputFormatter(OutputMode.HUMAN)
    formatter.finalize()

    captured = capsys.readouterr()
    assert captured.out == ""


def test_finalize_ndjson_no_op(capsys: pytest.CaptureFixture[str]) -> None:
    """NDJSON mode finalize should do nothing (already streamed)."""
    formatter = OutputFormatter(OutputMode.NDJSON)
    formatter.finalize()

    captured = capsys.readouterr()
    assert captured.out == ""


def test_json_workflow(capsys: pytest.CaptureFixture[str]) -> None:
    """Test complete JSON output workflow."""
    formatter = OutputFormatter(OutputMode.JSON)

    # Emit several records
    formatter.emit({"name": "workspace1", "path": "/path/1"})
    formatter.emit({"name": "workspace2", "path": "/path/2"})

    # Nothing output yet
    captured = capsys.readouterr()
    assert captured.out == ""

    # Finalize outputs everything
    formatter.finalize()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2


def test_ndjson_workflow(capsys: pytest.CaptureFixture[str]) -> None:
    """Test complete NDJSON output workflow."""
    formatter = OutputFormatter(OutputMode.NDJSON)

    # Each emit outputs immediately
    formatter.emit({"name": "workspace1"})
    captured = capsys.readouterr()
    assert json.loads(captured.out.strip()) == {"name": "workspace1"}

    formatter.emit({"name": "workspace2"})
    captured = capsys.readouterr()
    assert json.loads(captured.out.strip()) == {"name": "workspace2"}

    # Finalize is no-op
    formatter.finalize()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_human_workflow(capsys: pytest.CaptureFixture[str]) -> None:
    """Test complete HUMAN output workflow."""
    formatter = OutputFormatter(OutputMode.HUMAN)

    # emit does nothing in human mode
    formatter.emit({"name": "ignored"})

    # emit_text outputs text
    formatter.emit_text("Workspace: test")
    formatter.emit_text("  Path: /path/to/test")

    captured = capsys.readouterr()
    assert "Workspace: test" in captured.out
    assert "Path: /path/to/test" in captured.out

    # Finalize is no-op
    formatter.finalize()
    captured = capsys.readouterr()
    assert captured.out == ""
