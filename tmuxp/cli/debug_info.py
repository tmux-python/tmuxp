import os
import pathlib
import platform
import shutil
import sys

import click

from libtmux import __version__ as libtmux_version
from libtmux.common import get_version, tmux_cmd

from ..__about__ import __version__
from .utils import tmuxp_echo

tmuxp_path = pathlib.Path(__file__).parent.parent


@click.command(name="debug-info", short_help="Print out all diagnostic info")
def command_debug_info():
    """
    Print debug info to submit with Issues.
    """

    def prepend_tab(strings):
        """
        Prepend tab to strings in list.
        """
        return list(map(lambda x: "\t%s" % x, strings))

    def output_break():
        """
        Generate output break.
        """
        return "-" * 25

    def format_tmux_resp(std_resp):
        """
        Format tmux command response for tmuxp stdout.
        """
        return "\n".join(
            [
                "\n".join(prepend_tab(std_resp.stdout)),
                click.style("\n".join(prepend_tab(std_resp.stderr)), fg="red"),
            ]
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
                ]
            )
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
