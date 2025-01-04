"""CLI for ``tmuxp debug-info`` subcommand."""

from __future__ import annotations

import os
import pathlib
import platform
import shutil
import sys
import typing as t

from colorama import Fore
from libtmux.__about__ import __version__ as libtmux_version
from libtmux.common import get_version, tmux_cmd

from tmuxp.__about__ import __version__

from .utils import tmuxp_echo

if t.TYPE_CHECKING:
    import argparse

tmuxp_path = pathlib.Path(__file__).parent.parent


def create_debug_info_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``debug-info`` subcommand."""
    return parser


def command_debug_info(
    parser: argparse.ArgumentParser | None = None,
) -> None:
    """Entrypoint for ``tmuxp debug-info`` to print debug info to submit with issues."""

    def prepend_tab(strings: list[str]) -> list[str]:
        """Prepend tab to strings in list."""
        return [f"\t{x}" for x in strings]

    def output_break() -> str:
        """Generate output break."""
        return "-" * 25

    def format_tmux_resp(std_resp: tmux_cmd) -> str:
        """Format tmux command response for tmuxp stdout."""
        return "\n".join(
            [
                "\n".join(prepend_tab(std_resp.stdout)),
                Fore.RED,
                "\n".join(prepend_tab(std_resp.stderr)),
                Fore.RESET,
            ],
        )

    output = [
        output_break(),
        "environment:\n{}".format(
            "\n".join(
                prepend_tab(
                    [
                        f"dist: {platform.platform()}",
                        f"arch: {platform.machine()}",
                        "uname: {}".format("; ".join(platform.uname()[:3])),
                        f"version: {platform.version()}",
                    ],
                ),
            ),
        ),
        output_break(),
        "python version: {}".format(" ".join(sys.version.split("\n"))),
        "system PATH: {}".format(os.environ["PATH"]),
        f"tmux version: {get_version()}",
        f"libtmux version: {libtmux_version}",
        f"tmuxp version: {__version__}",
        "tmux path: {}".format(shutil.which("tmux")),
        f"tmuxp path: {tmuxp_path}",
        "shell: {}".format(os.environ["SHELL"]),
        output_break(),
        "tmux sessions:\n{}".format(format_tmux_resp(tmux_cmd("list-sessions"))),
        "tmux windows:\n{}".format(format_tmux_resp(tmux_cmd("list-windows"))),
        "tmux panes:\n{}".format(format_tmux_resp(tmux_cmd("list-panes"))),
        "tmux global options:\n{}".format(
            format_tmux_resp(tmux_cmd("show-options", "-g")),
        ),
        "tmux window options:\n{}".format(
            format_tmux_resp(tmux_cmd("show-window-options", "-g")),
        ),
    ]

    tmuxp_echo("\n".join(output))
