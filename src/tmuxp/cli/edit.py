import argparse
import os
import pathlib
import subprocess
import typing as t

from .utils import scan_config


def create_edit_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    parser.add_argument(
        dest="config_file",
        metavar="config-file",
        type=str,
        help="checks current tmuxp and current directory for config files.",
    )
    return parser


def command_edit(
    config_file: t.Union[str, pathlib.Path],
    parser: t.Optional[argparse.ArgumentParser] = None,
):
    config_file = scan_config(config_file)

    sys_editor = os.environ.get("EDITOR", "vim")
    subprocess.call([sys_editor, config_file])
