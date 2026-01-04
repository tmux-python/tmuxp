"""Custom help formatter for tmuxp CLI with colorized examples.

This module provides a custom argparse formatter that colorizes example
sections in help output, similar to vcspull's formatter.

Examples
--------
>>> from tmuxp.cli._formatter import TmuxpHelpFormatter
>>> TmuxpHelpFormatter  # doctest: +ELLIPSIS
<class '...TmuxpHelpFormatter'>
"""

from __future__ import annotations

import argparse
import re
import typing as t

# Options that expect a value (set externally or via --option=value)
OPTIONS_EXPECTING_VALUE = frozenset(
    {
        "-f",
        "--file",
        "-s",
        "--socket-name",
        "-S",
        "--socket-path",
        "-L",
        "--log-level",
        "-c",
        "--command",
        "-t",
        "--target",
        "-o",
        "--output",
        "-d",
        "--dir",
        "--color",
        "-w",
        "--workspace",
    }
)

# Standalone flag options (no value)
OPTIONS_FLAG_ONLY = frozenset(
    {
        "-h",
        "--help",
        "-V",
        "--version",
        "-y",
        "--yes",
        "-n",
        "--no",
        "-d",
        "--detached",
        "-2",
        "-8",
        "-a",
        "--append",
        "--json",
        "--raw",
    }
)


class TmuxpHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Help formatter with colorized examples for tmuxp CLI.

    This formatter extends RawDescriptionHelpFormatter to preserve formatting
    of description text while adding syntax highlighting to example sections.

    The formatter uses a `_theme` attribute (set externally) to apply colors.
    If no theme is set, the formatter falls back to plain text output.

    Examples
    --------
    >>> formatter = TmuxpHelpFormatter("tmuxp")
    >>> formatter  # doctest: +ELLIPSIS
    <...TmuxpHelpFormatter object at ...>
    """

    def _fill_text(self, text: str, width: int, indent: str) -> str:
        """Fill text, colorizing examples sections if theme is available.

        Parameters
        ----------
        text : str
            Text to format.
        width : int
            Maximum line width.
        indent : str
            Indentation prefix.

        Returns
        -------
        str
            Formatted text, with colorized examples if theme is set.
        """
        theme = getattr(self, "_theme", None)
        if not text or theme is None:
            return super()._fill_text(text, width, indent)

        lines = text.splitlines(keepends=True)
        formatted_lines: list[str] = []
        in_examples_block = False
        expect_value = False

        for line in lines:
            if line.strip() == "":
                in_examples_block = False
                expect_value = False
                formatted_lines.append(f"{indent}{line}")
                continue

            has_newline = line.endswith("\n")
            stripped_line = line.rstrip("\n")
            leading_length = len(stripped_line) - len(stripped_line.lstrip(" "))
            leading = stripped_line[:leading_length]
            content = stripped_line[leading_length:]
            content_lower = content.lower()
            is_section_heading = (
                content_lower.endswith("examples:") and content_lower != "examples:"
            )

            if is_section_heading or content_lower == "examples:":
                formatted_content = f"{theme.heading}{content}{theme.reset}"
                in_examples_block = True
                expect_value = False
            elif in_examples_block:
                colored_content = self._colorize_example_line(
                    content,
                    theme=theme,
                    expect_value=expect_value,
                )
                expect_value = colored_content.expect_value
                formatted_content = colored_content.text
            else:
                formatted_content = stripped_line

            newline = "\n" if has_newline else ""
            formatted_lines.append(f"{indent}{leading}{formatted_content}{newline}")

        return "".join(formatted_lines)

    class _ColorizedLine(t.NamedTuple):
        """Result of colorizing an example line."""

        text: str
        expect_value: bool

    def _colorize_example_line(
        self,
        content: str,
        *,
        theme: t.Any,
        expect_value: bool,
    ) -> _ColorizedLine:
        """Colorize a single example command line.

        Parameters
        ----------
        content : str
            The line content to colorize.
        theme : Any
            Theme object with color attributes (prog, action, etc.).
        expect_value : bool
            Whether the previous token expects a value.

        Returns
        -------
        _ColorizedLine
            Named tuple with colorized text and updated expect_value state.
        """
        parts: list[str] = []
        expecting_value = expect_value
        first_token = True
        colored_subcommand = False

        for match in re.finditer(r"\s+|\S+", content):
            token = match.group()
            if token.isspace():
                parts.append(token)
                continue

            if expecting_value:
                color = theme.label
                expecting_value = False
            elif token.startswith("--"):
                color = theme.long_option
                expecting_value = (
                    token not in OPTIONS_FLAG_ONLY and token in OPTIONS_EXPECTING_VALUE
                )
            elif token.startswith("-"):
                color = theme.short_option
                expecting_value = (
                    token not in OPTIONS_FLAG_ONLY and token in OPTIONS_EXPECTING_VALUE
                )
            elif first_token:
                color = theme.prog
            elif not colored_subcommand:
                color = theme.action
                colored_subcommand = True
            else:
                color = None

            first_token = False

            if color:
                parts.append(f"{color}{token}{theme.reset}")
            else:
                parts.append(token)

        return self._ColorizedLine(text="".join(parts), expect_value=expecting_value)


class HelpTheme(t.NamedTuple):
    """Theme colors for help output.

    Examples
    --------
    >>> from tmuxp.cli._formatter import HelpTheme
    >>> theme = HelpTheme.from_colors(None)
    >>> theme.reset
    ''
    """

    prog: str
    action: str
    long_option: str
    short_option: str
    label: str
    heading: str
    reset: str

    @classmethod
    def from_colors(cls, colors: t.Any) -> HelpTheme:
        """Create theme from Colors instance.

        Parameters
        ----------
        colors : Colors | None
            Colors instance, or None for no colors.

        Returns
        -------
        HelpTheme
            Theme with ANSI codes if colors enabled, empty strings otherwise.

        Examples
        --------
        >>> from tmuxp.cli._colors import Colors, ColorMode
        >>> from tmuxp.cli._formatter import HelpTheme
        >>> colors = Colors(ColorMode.NEVER)
        >>> theme = HelpTheme.from_colors(colors)
        >>> theme.reset
        ''
        """
        if colors is None or not colors._enabled:
            return cls(
                prog="",
                action="",
                long_option="",
                short_option="",
                label="",
                heading="",
                reset="",
            )

        # Import style here to avoid circular import
        from tmuxp.cli._colors import style

        return cls(
            prog=style("", fg="magenta", bold=True).rstrip("\033[0m"),
            action=style("", fg="cyan").rstrip("\033[0m"),
            long_option=style("", fg="green").rstrip("\033[0m"),
            short_option=style("", fg="green").rstrip("\033[0m"),
            label=style("", fg="yellow").rstrip("\033[0m"),
            heading=style("", fg="blue").rstrip("\033[0m"),
            reset="\033[0m",
        )
