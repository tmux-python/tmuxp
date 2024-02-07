"""CLI for ``tmuxp debug-info`` subcommand."""
import argparse
import os
import pathlib
import platform
import shutil
import sys
import typing as t

from colorama import Fore
from libtmux.__about__ import __version__ as libtmux_version
from libtmux.common import get_version, tmux_cmd

from ..__about__ import __version__
from .utils import tmuxp_echo

tmuxp_path = pathlib.Path(__file__).parent.parent


def create_debug_info_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``debug-info`` subcommand."""
    return parser


def command_debug_info(
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
    """Entrypoint for ``tmuxp debug-info`` to print debug info to submit with issues."""

    def prepend_tab(strings: t.List[str]) -> t.List[str]:
        """Prepend tab to strings in list."""
        return ["\t%s" % x for x in strings]

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
        "environment:\n%s"
        % "\n".join(
            prepend_tab(
                [
                    "dist: %s" % platform.platform(),
                    "arch: %s" % platform.machine(),
                    "uname: %s" % "; ".join(platform.uname()[:3]),
                    "version: %s" % platform.version(),
                ],
            ),
        ),
        output_break(),
        "python version: %s" % " ".join(sys.version.split("\n")),
        "system PATH: %s" % os.environ["PATH"],
        "tmux version: %s" % get_version(),
        "libtmux version: %s" % libtmux_version,
        "tmuxp version: %s" % __version__,
        "tmux path: %s" % shutil.which("tmux"),
        "tmuxp path: %s" % tmuxp_path,
        "shell: %s" % os.environ["SHELL"],
        output_break(),
        "tmux sessions:\n%s" % format_tmux_resp(tmux_cmd("list-sessions")),
        "tmux windows:\n%s" % format_tmux_resp(tmux_cmd("list-windows")),
        "tmux panes:\n%s" % format_tmux_resp(tmux_cmd("list-panes")),
        "tmux global options:\n%s" % format_tmux_resp(tmux_cmd("show-options", "-g")),
        "tmux window options:\n%s"
        % format_tmux_resp(tmux_cmd("show-window-options", "-g")),
    ]

    tmuxp_echo("\n".join(output))
