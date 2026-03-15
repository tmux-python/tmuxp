"""CLI for ``tmuxp stop`` subcommand."""

from __future__ import annotations

import argparse
import logging
import typing as t

from libtmux.server import Server

from tmuxp import exc, util
from tmuxp.exc import TmuxpException

from ._colors import Colors, build_description, get_color_mode
from .utils import tmuxp_echo

logger = logging.getLogger(__name__)

STOP_DESCRIPTION = build_description(
    """
    Stop (kill) a tmux session.
    """,
    (
        (
            None,
            [
                "tmuxp stop mysession",
                "tmuxp stop -L mysocket mysession",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    CLIColorModeLiteral: t.TypeAlias = t.Literal["auto", "always", "never"]


class CLIStopNamespace(argparse.Namespace):
    """Typed :class:`argparse.Namespace` for tmuxp stop command."""

    color: CLIColorModeLiteral
    session_name: str | None
    socket_name: str | None
    socket_path: str | None


def create_stop_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``stop`` subcommand."""
    parser.add_argument(
        dest="session_name",
        metavar="session-name",
        nargs="?",
        action="store",
    )
    parser.add_argument(
        "-S",
        dest="socket_path",
        metavar="socket-path",
        help="pass-through for tmux -S",
    )
    parser.add_argument(
        "-L",
        dest="socket_name",
        metavar="socket-name",
        help="pass-through for tmux -L",
    )
    return parser


def command_stop(
    args: CLIStopNamespace,
    parser: argparse.ArgumentParser | None = None,
) -> None:
    """Entrypoint for ``tmuxp stop``, kill a tmux session."""
    color_mode = get_color_mode(args.color)
    colors = Colors(color_mode)

    server = Server(socket_name=args.socket_name, socket_path=args.socket_path)

    try:
        if args.session_name:
            session = server.sessions.get(
                session_name=args.session_name,
                default=None,
            )
        else:
            session = util.get_session(server)

        if not session:
            raise exc.SessionNotFound(args.session_name)
    except TmuxpException as e:
        tmuxp_echo(colors.error(str(e)))
        return

    session_name = session.name

    # Run on_project_stop hook from session environment
    on_stop_cmd = session.getenv("TMUXP_ON_PROJECT_STOP")
    if on_stop_cmd and isinstance(on_stop_cmd, str):
        start_dir = session.getenv("TMUXP_START_DIRECTORY")
        _stop_cwd = str(start_dir) if isinstance(start_dir, str) else None
        util.run_hook_commands(on_stop_cmd, cwd=_stop_cwd)

    session.kill()
    logger.info("session stopped", extra={"tmux_session": session_name or ""})
    tmuxp_echo(
        colors.success("Stopped ") + colors.highlight(session_name or ""),
    )
