"""CLI for ``tmuxp debug-info`` subcommand."""

from __future__ import annotations

import argparse
import os
import pathlib
import platform
import shutil
import sys
import typing as t

from libtmux.__about__ import __version__ as libtmux_version
from libtmux.common import get_version, tmux_cmd

from tmuxp.__about__ import __version__
from tmuxp._internal.private_path import PrivatePath, collapse_home_in_string

from ._colors import Colors, build_description, get_color_mode
from .utils import tmuxp_echo

DEBUG_INFO_DESCRIPTION = build_description(
    """
    Print diagnostic information for debugging and issue reports.
    """,
    (
        (
            None,
            [
                "tmuxp debug-info",
            ],
        ),
        (
            "Machine-readable output examples",
            [
                "tmuxp debug-info --json",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    from typing import TypeAlias

    CLIColorModeLiteral: TypeAlias = t.Literal["auto", "always", "never"]

tmuxp_path = pathlib.Path(__file__).parent.parent


class CLIDebugInfoNamespace(argparse.Namespace):
    """Typed :class:`argparse.Namespace` for tmuxp debug-info command."""

    color: CLIColorModeLiteral
    output_json: bool


def create_debug_info_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``debug-info`` subcommand."""
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="output as JSON",
    )
    return parser


def _private(path: pathlib.Path | str | None) -> str:
    """Privacy-mask a path by collapsing home directory to ~.

    Parameters
    ----------
    path : pathlib.Path | str | None
        Path to mask.

    Returns
    -------
    str
        Path with home directory replaced by ~.

    Examples
    --------
    >>> _private(None)
    ''
    >>> _private('')
    ''
    >>> _private('/usr/bin/tmux')
    '/usr/bin/tmux'
    """
    if path is None or path == "":
        return ""
    return str(PrivatePath(path))


def _collect_debug_info() -> dict[str, t.Any]:
    """Collect debug information as a structured dictionary.

    All paths are privacy-masked using PrivatePath (home → ~).

    Returns
    -------
    dict[str, Any]
        Debug information with environment, versions, paths, and tmux state.

    Examples
    --------
    >>> data = _collect_debug_info()
    >>> 'environment' in data
    True
    >>> 'tmux_version' in data
    True
    """
    # Collect tmux command outputs
    sessions_resp = tmux_cmd("list-sessions")
    windows_resp = tmux_cmd("list-windows")
    panes_resp = tmux_cmd("list-panes")
    global_opts_resp = tmux_cmd("show-options", "-g")
    window_opts_resp = tmux_cmd("show-window-options", "-g")

    return {
        "environment": {
            "dist": platform.platform(),
            "arch": platform.machine(),
            "uname": list(platform.uname()[:3]),
            "version": platform.version(),
        },
        "python_version": " ".join(sys.version.split("\n")),
        "system_path": collapse_home_in_string(os.environ.get("PATH", "")),
        "tmux_version": str(get_version()),
        "libtmux_version": libtmux_version,
        "tmuxp_version": __version__,
        "tmux_path": _private(shutil.which("tmux")),
        "tmuxp_path": _private(tmuxp_path),
        "shell": _private(os.environ.get("SHELL", "")),
        "tmux": {
            "sessions": sessions_resp.stdout,
            "windows": windows_resp.stdout,
            "panes": panes_resp.stdout,
            "global_options": global_opts_resp.stdout,
            "window_options": window_opts_resp.stdout,
        },
    }


def _format_human_output(data: dict[str, t.Any], colors: Colors) -> str:
    """Format debug info as human-readable colored output.

    Parameters
    ----------
    data : dict[str, Any]
        Debug information dictionary.
    colors : Colors
        Color manager for formatting.

    Returns
    -------
    str
        Formatted human-readable output.

    Examples
    --------
    >>> from tmuxp.cli._colors import ColorMode, Colors
    >>> colors = Colors(ColorMode.NEVER)
    >>> data = {
    ...     "environment": {
    ...         "dist": "Linux",
    ...         "arch": "x86_64",
    ...         "uname": ["Linux", "host", "6.0"],
    ...         "version": "#1 SMP",
    ...     },
    ...     "python_version": "3.12.0",
    ...     "system_path": "/usr/bin",
    ...     "tmux_version": "3.4",
    ...     "libtmux_version": "0.40.0",
    ...     "tmuxp_version": "1.50.0",
    ...     "tmux_path": "/usr/bin/tmux",
    ...     "tmuxp_path": "~/tmuxp",
    ...     "shell": "/bin/bash",
    ...     "tmux": {
    ...         "sessions": [],
    ...         "windows": [],
    ...         "panes": [],
    ...         "global_options": [],
    ...         "window_options": [],
    ...     },
    ... }
    >>> output = _format_human_output(data, colors)
    >>> "environment" in output
    True
    """

    def format_tmux_section(lines: list[str]) -> str:
        """Format tmux command output with syntax highlighting."""
        formatted_lines = []
        for line in lines:
            formatted = colors.format_tmux_option(line)
            formatted_lines.append(f"\t{formatted}")
        return "\n".join(formatted_lines)

    env = data["environment"]
    env_items = [
        f"\t{colors.format_kv('dist', env['dist'])}",
        f"\t{colors.format_kv('arch', env['arch'])}",
        f"\t{colors.format_kv('uname', '; '.join(env['uname']))}",
        f"\t{colors.format_kv('version', env['version'])}",
    ]

    tmux_data = data["tmux"]
    output = [
        colors.format_separator(),
        f"{colors.format_label('environment')}:\n" + "\n".join(env_items),
        colors.format_separator(),
        colors.format_kv("python version", data["python_version"]),
        colors.format_kv("system PATH", data["system_path"]),
        colors.format_kv("tmux version", colors.format_version(data["tmux_version"])),
        colors.format_kv(
            "libtmux version", colors.format_version(data["libtmux_version"])
        ),
        colors.format_kv("tmuxp version", colors.format_version(data["tmuxp_version"])),
        colors.format_kv("tmux path", colors.format_path(data["tmux_path"])),
        colors.format_kv("tmuxp path", colors.format_path(data["tmuxp_path"])),
        colors.format_kv("shell", data["shell"]),
        colors.format_separator(),
        f"{colors.format_label('tmux sessions')}:\n"
        + format_tmux_section(tmux_data["sessions"]),
        f"{colors.format_label('tmux windows')}:\n"
        + format_tmux_section(tmux_data["windows"]),
        f"{colors.format_label('tmux panes')}:\n"
        + format_tmux_section(tmux_data["panes"]),
        f"{colors.format_label('tmux global options')}:\n"
        + format_tmux_section(tmux_data["global_options"]),
        f"{colors.format_label('tmux window options')}:\n"
        + format_tmux_section(tmux_data["window_options"]),
    ]

    return "\n".join(output)


def command_debug_info(
    args: CLIDebugInfoNamespace | None = None,
    parser: argparse.ArgumentParser | None = None,
) -> None:
    """Entrypoint for ``tmuxp debug-info`` to print debug info to submit with issues."""
    import json
    import sys

    # Get output mode
    output_json = args.output_json if args else False

    # Get color mode (only used for human output)
    color_mode = get_color_mode(args.color if args else None)
    colors = Colors(color_mode)

    # Collect debug info
    data = _collect_debug_info()

    # Output based on mode
    if output_json:
        # Single object, not wrapped in array
        sys.stdout.write(json.dumps(data, indent=2) + "\n")
        sys.stdout.flush()
    else:
        tmuxp_echo(_format_human_output(data, colors))
