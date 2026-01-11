"""Output formatting utilities for tmuxp CLI.

Provides structured output modes (JSON, NDJSON) alongside human-readable output.

Examples
--------
>>> from tmuxp.cli._output import OutputMode, OutputFormatter, get_output_mode

Get output mode from flags:

>>> get_output_mode(json_flag=False, ndjson_flag=False)
<OutputMode.HUMAN: 'human'>
>>> get_output_mode(json_flag=True, ndjson_flag=False)
<OutputMode.JSON: 'json'>
>>> get_output_mode(json_flag=False, ndjson_flag=True)
<OutputMode.NDJSON: 'ndjson'>

NDJSON takes precedence over JSON:

>>> get_output_mode(json_flag=True, ndjson_flag=True)
<OutputMode.NDJSON: 'ndjson'>
"""

from __future__ import annotations

import enum
import json
import sys
import typing as t


class OutputMode(enum.Enum):
    """Output format modes for CLI commands.

    Examples
    --------
    >>> OutputMode.HUMAN.value
    'human'
    >>> OutputMode.JSON.value
    'json'
    >>> OutputMode.NDJSON.value
    'ndjson'
    """

    HUMAN = "human"
    JSON = "json"
    NDJSON = "ndjson"


class OutputFormatter:
    """Manage output formatting for different modes (human, JSON, NDJSON).

    Parameters
    ----------
    mode : OutputMode
        The output mode to use (human, json, ndjson). Default is HUMAN.

    Examples
    --------
    >>> formatter = OutputFormatter(OutputMode.JSON)
    >>> formatter.mode
    <OutputMode.JSON: 'json'>

    >>> formatter = OutputFormatter()
    >>> formatter.mode
    <OutputMode.HUMAN: 'human'>
    """

    def __init__(self, mode: OutputMode = OutputMode.HUMAN) -> None:
        """Initialize the output formatter."""
        self.mode = mode
        self._json_buffer: list[dict[str, t.Any]] = []

    def emit(self, data: dict[str, t.Any]) -> None:
        """Emit a data event.

        In NDJSON mode, immediately writes one JSON object per line.
        In JSON mode, buffers data for later output as a single array.
        In HUMAN mode, does nothing (use emit_text for human output).

        Parameters
        ----------
        data : dict
            Event data to emit as JSON.

        Examples
        --------
        >>> formatter = OutputFormatter(OutputMode.JSON)
        >>> formatter.emit({"name": "test", "path": "/tmp"})
        >>> len(formatter._json_buffer)
        1
        """
        if self.mode == OutputMode.NDJSON:
            # Stream one JSON object per line immediately
            sys.stdout.write(json.dumps(data) + "\n")
            sys.stdout.flush()
        elif self.mode == OutputMode.JSON:
            # Buffer for later output as single array
            self._json_buffer.append(data)
        # Human mode: handled by specific command implementations

    def emit_text(self, text: str) -> None:
        """Emit human-readable text (only in HUMAN mode).

        Parameters
        ----------
        text : str
            Text to output.

        Examples
        --------
        >>> import io
        >>> formatter = OutputFormatter(OutputMode.JSON)
        >>> formatter.emit_text("This won't print")  # No output in JSON mode
        """
        if self.mode == OutputMode.HUMAN:
            sys.stdout.write(text + "\n")
            sys.stdout.flush()

    def finalize(self) -> None:
        """Finalize output (flush JSON buffer if needed).

        In JSON mode, outputs the buffered data as a formatted JSON array.
        In other modes, does nothing.

        Examples
        --------
        >>> formatter = OutputFormatter(OutputMode.JSON)
        >>> formatter.emit({"name": "test1"})
        >>> formatter.emit({"name": "test2"})
        >>> len(formatter._json_buffer)
        2
        >>> # formatter.finalize() would print the JSON array
        """
        if self.mode == OutputMode.JSON and self._json_buffer:
            sys.stdout.write(json.dumps(self._json_buffer, indent=2) + "\n")
            sys.stdout.flush()
            self._json_buffer.clear()


def get_output_mode(json_flag: bool, ndjson_flag: bool) -> OutputMode:
    """Determine output mode from command flags.

    NDJSON takes precedence over JSON if both are specified.

    Parameters
    ----------
    json_flag : bool
        Whether --json was specified.
    ndjson_flag : bool
        Whether --ndjson was specified.

    Returns
    -------
    OutputMode
        The determined output mode.

    Examples
    --------
    >>> get_output_mode(json_flag=False, ndjson_flag=False)
    <OutputMode.HUMAN: 'human'>
    >>> get_output_mode(json_flag=True, ndjson_flag=False)
    <OutputMode.JSON: 'json'>
    >>> get_output_mode(json_flag=False, ndjson_flag=True)
    <OutputMode.NDJSON: 'ndjson'>
    >>> get_output_mode(json_flag=True, ndjson_flag=True)
    <OutputMode.NDJSON: 'ndjson'>
    """
    if ndjson_flag:
        return OutputMode.NDJSON
    if json_flag:
        return OutputMode.JSON
    return OutputMode.HUMAN
