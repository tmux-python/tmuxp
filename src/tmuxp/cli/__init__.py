"""CLI utilities for tmuxp."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import typing as t

from libtmux.__about__ import __version__ as libtmux_version
from libtmux.common import has_minimum_version
from libtmux.exc import TmuxCommandNotFound

from tmuxp import exc
from tmuxp.__about__ import __version__
from tmuxp.log import setup_logger

from ._colors import build_description
from ._formatter import TmuxpHelpFormatter, create_themed_formatter
from .convert import CONVERT_DESCRIPTION, command_convert, create_convert_subparser
from .debug_info import (
    DEBUG_INFO_DESCRIPTION,
    CLIDebugInfoNamespace,
    command_debug_info,
    create_debug_info_subparser,
)
from .edit import EDIT_DESCRIPTION, command_edit, create_edit_subparser
from .freeze import (
    FREEZE_DESCRIPTION,
    CLIFreezeNamespace,
    command_freeze,
    create_freeze_subparser,
)
from .import_config import (
    IMPORT_DESCRIPTION,
    command_import_teamocil,
    command_import_tmuxinator,
    create_import_subparser,
)
from .load import (
    LOAD_DESCRIPTION,
    CLILoadNamespace,
    command_load,
    create_load_subparser,
)
from .ls import LS_DESCRIPTION, CLILsNamespace, command_ls, create_ls_subparser
from .search import (
    SEARCH_DESCRIPTION,
    CLISearchNamespace,
    command_search,
    create_search_subparser,
)
from .shell import (
    SHELL_DESCRIPTION,
    CLIShellNamespace,
    command_shell,
    create_shell_subparser,
)
from .utils import tmuxp_echo

logger = logging.getLogger(__name__)

CLI_DESCRIPTION = build_description(
    """
    tmuxp - tmux session manager.

    Manage and launch tmux sessions from YAML/JSON workspace files.
    """,
    (
        (
            "load",
            [
                "tmuxp load myproject",
                "tmuxp load ./workspace.yaml",
                "tmuxp load -d myproject",
                "tmuxp load -y dev staging",
            ],
        ),
        (
            "freeze",
            [
                "tmuxp freeze mysession",
                "tmuxp freeze mysession -o session.yaml",
            ],
        ),
        (
            "ls",
            [
                "tmuxp ls",
                "tmuxp ls --tree",
                "tmuxp ls --full",
                "tmuxp ls --json",
            ],
        ),
        (
            "search",
            [
                "tmuxp search dev",
                "tmuxp search name:myproject",
                "tmuxp search -i DEV",
                "tmuxp search --json dev",
            ],
        ),
        (
            "shell",
            [
                "tmuxp shell",
                "tmuxp shell -L mysocket",
                "tmuxp shell -c 'print(server.sessions)'",
            ],
        ),
        (
            "convert",
            [
                "tmuxp convert workspace.yaml",
                "tmuxp convert workspace.json",
            ],
        ),
        (
            "import",
            [
                "tmuxp import teamocil ~/.teamocil/project.yml",
                "tmuxp import tmuxinator ~/.tmuxinator/project.yml",
            ],
        ),
        (
            "edit",
            [
                "tmuxp edit myproject",
            ],
        ),
        (
            "debug-info",
            [
                "tmuxp debug-info",
                "tmuxp debug-info --json",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    import pathlib
    from typing import TypeAlias

    CLIVerbosity: TypeAlias = t.Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    CLIColorMode: TypeAlias = t.Literal["auto", "always", "never"]
    CLISubparserName: TypeAlias = t.Literal[
        "ls",
        "load",
        "freeze",
        "convert",
        "edit",
        "import",
        "search",
        "shell",
        "debug-info",
    ]
    CLIImportSubparserName: TypeAlias = t.Literal["teamocil", "tmuxinator"]


def create_parser() -> argparse.ArgumentParser:
    """Create CLI :class:`argparse.ArgumentParser` for tmuxp."""
    # Use factory to create themed formatter with auto-detected color mode
    # This respects NO_COLOR, FORCE_COLOR env vars and TTY detection
    formatter_class = create_themed_formatter()

    parser = argparse.ArgumentParser(
        prog="tmuxp",
        description=CLI_DESCRIPTION,
        formatter_class=formatter_class,
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {__version__}, libtmux {libtmux_version}",
    )
    parser.add_argument(
        "--log-level",
        action="store",
        metavar="log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help='log level (debug, info, warning, error, critical) (default "info")',
    )
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="when to use colors: auto (default), always, or never",
    )
    subparsers = parser.add_subparsers(dest="subparser_name")
    load_parser = subparsers.add_parser(
        "load",
        help="load tmuxp workspaces",
        description=LOAD_DESCRIPTION,
        formatter_class=formatter_class,
    )
    create_load_subparser(load_parser)
    shell_parser = subparsers.add_parser(
        "shell",
        help="launch python shell for tmux server, session, window and pane",
        description=SHELL_DESCRIPTION,
        formatter_class=formatter_class,
    )
    create_shell_subparser(shell_parser)
    import_parser = subparsers.add_parser(
        "import",
        help="import workspaces from teamocil and tmuxinator.",
        description=IMPORT_DESCRIPTION,
        formatter_class=formatter_class,
    )
    create_import_subparser(import_parser)

    convert_parser = subparsers.add_parser(
        "convert",
        help="convert workspace files between yaml and json.",
        description=CONVERT_DESCRIPTION,
        formatter_class=formatter_class,
    )
    create_convert_subparser(convert_parser)

    debug_info_parser = subparsers.add_parser(
        "debug-info",
        help="print out all diagnostic info",
        description=DEBUG_INFO_DESCRIPTION,
        formatter_class=formatter_class,
    )
    create_debug_info_subparser(debug_info_parser)

    ls_parser = subparsers.add_parser(
        "ls",
        help="list workspaces in tmuxp directory",
        description=LS_DESCRIPTION,
        formatter_class=formatter_class,
    )
    create_ls_subparser(ls_parser)

    search_parser = subparsers.add_parser(
        "search",
        help="search workspace files by name, session, path, or content",
        description=SEARCH_DESCRIPTION,
        formatter_class=formatter_class,
    )
    create_search_subparser(search_parser)

    edit_parser = subparsers.add_parser(
        "edit",
        help="run $EDITOR on workspace file",
        description=EDIT_DESCRIPTION,
        formatter_class=formatter_class,
    )
    create_edit_subparser(edit_parser)

    freeze_parser = subparsers.add_parser(
        "freeze",
        help="freeze a live tmux session to a tmuxp workspace file",
        description=FREEZE_DESCRIPTION,
        formatter_class=formatter_class,
    )
    create_freeze_subparser(freeze_parser)

    return parser


class CLINamespace(argparse.Namespace):
    """Typed :class:`argparse.Namespace` for tmuxp root-level CLI."""

    log_level: CLIVerbosity
    color: CLIColorMode
    subparser_name: CLISubparserName
    import_subparser_name: CLIImportSubparserName | None
    version: bool


ns = CLINamespace()


def cli(_args: list[str] | None = None) -> None:
    """Manage tmux sessions.

    Pass the "--help" argument to any command to see detailed help.
    See detailed documentation and examples at:
    http://tmuxp.git-pull.com/
    """
    try:
        has_minimum_version()
    except TmuxCommandNotFound:
        tmuxp_echo("tmux not found. tmuxp requires you install tmux first.")
        sys.exit()
    except exc.TmuxpException as e:
        tmuxp_echo(str(e))
        sys.exit()

    parser = create_parser()
    args = parser.parse_args(_args, namespace=ns)

    setup_logger(logger=logger, level=args.log_level.upper())

    if args.subparser_name is None:
        parser.print_help()
        return
    if args.subparser_name == "load":
        command_load(
            args=CLILoadNamespace(**vars(args)),
            parser=parser,
        )
    elif args.subparser_name == "shell":
        command_shell(
            args=CLIShellNamespace(**vars(args)),
            parser=parser,
        )
    elif args.subparser_name == "import":
        import_subparser_name = getattr(args, "import_subparser_name", None)
        if import_subparser_name is None:
            parser.print_help()
            return
        if import_subparser_name == "teamocil":
            command_import_teamocil(
                workspace_file=args.workspace_file,
                parser=parser,
                color=args.color,
            )
        elif import_subparser_name == "tmuxinator":
            command_import_tmuxinator(
                workspace_file=args.workspace_file,
                parser=parser,
                color=args.color,
            )
    elif args.subparser_name == "convert":
        command_convert(
            workspace_file=args.workspace_file,
            answer_yes=args.answer_yes,
            parser=parser,
            color=args.color,
        )
    elif args.subparser_name == "debug-info":
        command_debug_info(
            args=CLIDebugInfoNamespace(**vars(args)),
            parser=parser,
        )

    elif args.subparser_name == "edit":
        command_edit(
            workspace_file=args.workspace_file,
            parser=parser,
            color=args.color,
        )
    elif args.subparser_name == "freeze":
        command_freeze(
            args=CLIFreezeNamespace(**vars(args)),
            parser=parser,
        )
    elif args.subparser_name == "ls":
        command_ls(
            args=CLILsNamespace(**vars(args)),
            parser=parser,
        )
    elif args.subparser_name == "search":
        command_search(
            args=CLISearchNamespace(**vars(args)),
            parser=parser,
        )


def startup(config_dir: pathlib.Path) -> None:
    """
    Initialize CLI.

    Parameters
    ----------
    str : get_workspace_dir(): Config directory to search
    """
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
