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

from ._colors import Colors, get_color_mode
from .utils import tmuxp_echo

if t.TYPE_CHECKING:
    from typing import TypeAlias

    CLIColorModeLiteral: TypeAlias = t.Literal["auto", "always", "never"]

tmuxp_path = pathlib.Path(__file__).parent.parent


class CLIDebugInfoNamespace(argparse.Namespace):
    """Typed :class:`argparse.Namespace` for tmuxp debug-info command."""

    color: CLIColorModeLiteral


def create_debug_info_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``debug-info`` subcommand."""
    return parser


def command_debug_info(
    args: CLIDebugInfoNamespace | None = None,
    parser: argparse.ArgumentParser | None = None,
) -> None:
    """Entrypoint for ``tmuxp debug-info`` to print debug info to submit with issues."""
    # Get color mode from args or default to AUTO
    color_mode = get_color_mode(args.color if args else None)
    colors = Colors(color_mode)

    def private(path: pathlib.Path | str | None) -> str:
        """Privacy-mask a path by collapsing home directory to ~."""
        if path is None:
            return ""
        return str(PrivatePath(path))

    def format_tmux_resp(std_resp: tmux_cmd) -> str:
        """Format tmux command response with syntax highlighting."""
        stdout_lines = []
        for line in std_resp.stdout:
            formatted = colors.format_tmux_option(line)
            stdout_lines.append(f"\t{formatted}")

        stderr_formatted = ""
        if std_resp.stderr:
            stderr_lines = "\n".join(f"\t{line}" for line in std_resp.stderr)
            if stderr_lines.strip():
                stderr_formatted = colors.error(stderr_lines)

        return "\n".join(["\n".join(stdout_lines), stderr_formatted])

    # Build environment section with indented key-value pairs
    env_items = [
        f"\t{colors.format_kv('dist', platform.platform())}",
        f"\t{colors.format_kv('arch', platform.machine())}",
        f"\t{colors.format_kv('uname', '; '.join(platform.uname()[:3]))}",
        f"\t{colors.format_kv('version', platform.version())}",
    ]

    output = [
        colors.format_separator(),
        f"{colors.format_label('environment')}:\n" + "\n".join(env_items),
        colors.format_separator(),
        colors.format_kv(
            "python version",
            " ".join(sys.version.split("\n")),
        ),
        colors.format_kv(
            "system PATH",
            collapse_home_in_string(os.environ.get("PATH", "")),
        ),
        colors.format_kv("tmux version", colors.format_version(str(get_version()))),
        colors.format_kv("libtmux version", colors.format_version(libtmux_version)),
        colors.format_kv("tmuxp version", colors.format_version(__version__)),
        colors.format_kv(
            "tmux path",
            colors.format_path(private(shutil.which("tmux"))),
        ),
        colors.format_kv("tmuxp path", colors.format_path(private(tmuxp_path))),
        colors.format_kv("shell", private(os.environ.get("SHELL", ""))),
        colors.format_separator(),
        f"{colors.format_label('tmux sessions')}:\n"
        + format_tmux_resp(tmux_cmd("list-sessions")),
        f"{colors.format_label('tmux windows')}:\n"
        + format_tmux_resp(tmux_cmd("list-windows")),
        f"{colors.format_label('tmux panes')}:\n"
        + format_tmux_resp(tmux_cmd("list-panes")),
        f"{colors.format_label('tmux global options')}:\n"
        + format_tmux_resp(tmux_cmd("show-options", "-g")),
        f"{colors.format_label('tmux window options')}:\n"
        + format_tmux_resp(tmux_cmd("show-window-options", "-g")),
    ]

    tmuxp_echo("\n".join(output))
