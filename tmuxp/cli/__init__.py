"""CLI utilities for tmuxp.

tmuxp.cli
~~~~~~~~~

"""
import logging
import os
import sys

import click

from libtmux.__about__ import __version__ as libtmux_version
from libtmux.common import has_minimum_version
from libtmux.exc import TmuxCommandNotFound
from tmuxp.cli.ls import command_ls

from .. import exc
from ..__about__ import __version__
from ..log import setup_logger
from .convert import command_convert
from .debug_info import command_debug_info
from .edit import command_edit
from .freeze import command_freeze
from .import_config import command_import
from .load import command_load
from .shell import command_shell
from .utils import tmuxp_echo

logger = logging.getLogger(__name__)


@click.group(context_settings={"obj": {}, "help_option_names": ["-h", "--help"]})
@click.version_option(
    __version__,
    "-V",
    "--version",
    message=f"%(prog)s %(version)s, libtmux {libtmux_version}",
)
@click.option(
    "--log-level",
    default="INFO",
    help="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
def cli(log_level):
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
    setup_logger(logger=logger, level=log_level.upper())


def startup(config_dir):
    """
    Initialize CLI.

    Parameters
    ----------
    str : get_config_dir(): Config directory to search
    """

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)


# Register sub-commands here
cli.add_command(command_convert)
cli.add_command(command_edit)
cli.add_command(command_debug_info)
cli.add_command(command_load)
cli.add_command(command_ls)
cli.add_command(command_freeze)
cli.add_command(command_shell)
cli.add_command(command_import)
