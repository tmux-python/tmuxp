"""CLI utilities for tmuxp.

tmuxp.cli
~~~~~~~~~

"""
import argparse
import logging
import os
import sys

from libtmux.__about__ import __version__ as libtmux_version
from libtmux.common import has_minimum_version
from libtmux.exc import TmuxCommandNotFound

from .. import exc
from ..__about__ import __version__
from ..log import setup_logger
from .convert import command_convert, create_convert_subparser
from .debug_info import command_debug_info, create_debug_info_subparser
from .edit import command_edit, create_edit_subparser
from .freeze import command_freeze, create_freeze_subparser
from .import_config import (
    command_import_teamocil,
    command_import_tmuxinator,
    create_import_subparser,
)
from .load import command_load, create_load_subparser
from .ls import command_ls, create_ls_subparser
from .shell import command_shell, create_shell_subparser
from .utils import tmuxp_echo

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tmuxp")
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {__version__}, libtmux {libtmux_version}",
    )
    parser.add_argument(
        "--log-level",
        action="store",
        default="INFO",
        help="log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    subparsers = parser.add_subparsers(dest="subparser_name")
    load_parser = subparsers.add_parser("load", help="load tmuxp workspaces")
    create_load_subparser(load_parser)
    shell_parser = subparsers.add_parser(
        "shell", help="launch python shell for tmux server, session, window and pane"
    )
    create_shell_subparser(shell_parser)
    import_parser = subparsers.add_parser(
        "import", help="import configurations from teamocil and tmuxinator."
    )
    create_import_subparser(import_parser)

    convert_parser = subparsers.add_parser(
        "convert", help="convert configs between yaml and json."
    )
    create_convert_subparser(convert_parser)

    debug_info_parser = subparsers.add_parser(
        "debug-info", help="print out all diagnostic info"
    )
    create_debug_info_subparser(debug_info_parser)

    ls_parser = subparsers.add_parser("ls", help="list sessions in config directory")
    create_ls_subparser(ls_parser)

    edit_parser = subparsers.add_parser("edit", help="run $EDITOR on config")
    create_edit_subparser(edit_parser)

    freeze_parser = subparsers.add_parser(
        "freeze", help="freeze a live tmux session to a tmuxp config"
    )
    create_freeze_subparser(freeze_parser)

    return parser


def cli(args=None):
    """Manage tmux sessions.

    Pass the "--help" argument to any command to see detailed help.
    See detailed documentation and examples at:
    http://tmuxp.git-pull.com/"""

    try:
        has_minimum_version()
    except TmuxCommandNotFound:
        tmuxp_echo("tmux not found. tmuxp requires you install tmux first.")
        sys.exit()
    except exc.TmuxpException as e:
        tmuxp_echo(e, err=True)
        sys.exit()

    parser = create_parser()
    args = parser.parse_args(args)

    setup_logger(logger=logger, level=args.log_level.upper())

    if args.subparser_name is None:
        parser.print_help()
        return
    elif args.subparser_name == "load":
        command_load(
            config_file=args.config_file,
            socket_name=args.socket_name,
            socket_path=args.socket_path,
            tmux_config_file=args.tmux_config_file,
            new_session_name=args.new_session_name,
            answer_yes=args.answer_yes,
            detached=args.detached,
            append=args.append,
            colors=args.colors,
            log_file=args.log_file,
            parser=parser,
        )
    elif args.subparser_name == "shell":
        command_shell(
            session_name=args.session_name,
            window_name=args.window_name,
            socket_name=args.socket_name,
            socket_path=args.socket_path,
            command=args.command,
            shell=args.shell,
            use_pythonrc=args.use_pythonrc,
            use_vi_mode=args.use_vi_mode,
            parser=parser,
        )
    elif args.subparser_name == "import":
        import_subparser_name = getattr(args, "import_subparser_name", None)
        if import_subparser_name is None:
            parser.print_help()
            return
        elif import_subparser_name == "teamocil":
            command_import_teamocil(
                config_file=args.config_file,
                parser=parser,
            )
        elif import_subparser_name == "tmuxinator":
            command_import_tmuxinator(
                config_file=args.config_file,
                parser=parser,
            )
    elif args.subparser_name == "convert":
        command_convert(
            config_file=args.config_file,
            answer_yes=args.answer_yes,
            parser=parser,
        )
    elif args.subparser_name == "debug-info":
        command_debug_info(parser=parser)

    elif args.subparser_name == "edit":
        command_edit(
            config_file=args.config_file,
            parser=parser,
        )
    elif args.subparser_name == "freeze":
        command_freeze(
            session_name=args.session_name,
            socket_name=args.socket_name,
            socket_path=args.socket_path,
            config_format=args.config_format,
            save_to=args.save_to,
            answer_yes=args.answer_yes,
            quiet=args.quiet,
            force=args.force,
            parser=parser,
        )
    elif args.subparser_name == "ls":
        command_ls(parser=parser)


def startup(config_dir):
    """
    Initialize CLI.

    Parameters
    ----------
    str : get_config_dir(): Config directory to search
    """

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
