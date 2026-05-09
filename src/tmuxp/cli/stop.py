"""CLI for ``tmuxp stop`` subcommand.

Mirrors tmuxinator's ``stop`` command (cli.rb:300-322) — fires the
``on_project_stop`` hook before killing the session, but does NOT fire
``on_project_exit`` (that's tmuxinator's behavior in template-stop.erb).
"""

from __future__ import annotations

import argparse
import logging
import os
import pathlib
import typing as t

from libtmux.server import Server

from tmuxp._internal.config_reader import ConfigReader
from tmuxp.util import run_lifecycle_hook
from tmuxp.workspace.finders import find_workspace_file

from ._colors import Colors, build_description, get_color_mode
from .utils import tmuxp_echo

logger = logging.getLogger(__name__)

STOP_DESCRIPTION = build_description(
    "Stop a tmuxp-managed session, firing the on_project_stop hook first.",
    ((None, ["tmuxp stop myproject", "tmuxp stop -L mysocket myproject"]),),
)

if t.TYPE_CHECKING:
    from typing import TypeAlias

    CLIColorModeLiteral: TypeAlias = t.Literal["auto", "always", "never"]


class CLIStopNamespace(argparse.Namespace):
    """Typed namespace for ``tmuxp stop``."""

    workspace_file: str
    socket_name: str | None
    socket_path: str | None
    color: CLIColorModeLiteral | None


def create_stop_subparser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` for ``tmuxp stop``."""
    parser.add_argument(
        "workspace_file",
        metavar="workspace-file",
        help="config name (resolved via tmuxp workspace dir) or path",
    )
    parser.add_argument(
        "-L",
        dest="socket_name",
        action="store",
        help="passthru to tmux(1) -L",
    )
    parser.add_argument(
        "-S",
        dest="socket_path",
        action="store",
        help="passthru to tmux(1) -S",
    )
    return parser


def command_stop(
    args: CLIStopNamespace, parser: argparse.ArgumentParser | None = None
) -> None:
    """Entry point for ``tmuxp stop``."""
    colors = Colors(get_color_mode(args.color))

    workspace_file = pathlib.Path(find_workspace_file(args.workspace_file))
    raw = ConfigReader._from_file(workspace_file) or {}
    session_name = raw.get("session_name")
    if not session_name:
        tmuxp_echo(
            colors.error(
                f"Cannot determine session_name from {workspace_file}",
            ),
        )
        return

    server = Server(
        socket_name=args.socket_name,
        socket_path=args.socket_path,
    )
    if not server.is_alive() or not server.has_session(session_name):
        tmuxp_echo(
            colors.muted(
                f"No running session named {session_name!r}; nothing to stop.",
            ),
        )
        return

    # Run on_project_stop BEFORE killing (matches template-stop.erb:1-10).
    cwd_str = (
        os.path.dirname(workspace_file)
        if "start_directory" not in raw
        else raw["start_directory"]
    )
    run_lifecycle_hook(
        "on_project_stop",
        raw.get("on_project_stop"),
        cwd=pathlib.Path(cwd_str) if cwd_str else None,
    )

    server.kill_session(session_name)
    tmuxp_echo(colors.muted(f"Stopped {session_name!r}."))
