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
        dest="workspace_file",
        metavar="workspace-file",
        type=str,
        help="checks current tmuxp and current directory for config files.",
    )
    return parser


def command_edit(
    workspace_file: t.Union[str, pathlib.Path],
    parser: t.Optional[argparse.ArgumentParser] = None,
):
    workspace_file = scan_config(workspace_file)

    sys_editor = os.environ.get("EDITOR", "vim")
    subprocess.call([sys_editor, workspace_file])
