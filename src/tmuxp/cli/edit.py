"""CLI for ``tmuxp edit`` subcommand."""

from __future__ import annotations

import os
import subprocess
import typing as t

from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace.finders import find_workspace_file

from ._colors import Colors, build_description, get_color_mode

EDIT_DESCRIPTION = build_description(
    """
    Open tmuxp workspace file in your system editor ($EDITOR).
    """,
    (
        (
            None,
            [
                "tmuxp edit myproject",
                "tmuxp edit ./workspace.yaml",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    import argparse
    import pathlib
    from typing import TypeAlias

    CLIColorModeLiteral: TypeAlias = t.Literal["auto", "always", "never"]


def create_edit_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``edit`` subcommand."""
    parser.add_argument(
        dest="workspace_file",
        metavar="workspace-file",
        type=str,
        help="checks current tmuxp and current directory for workspace files.",
    )
    return parser


def command_edit(
    workspace_file: str | pathlib.Path,
    parser: argparse.ArgumentParser | None = None,
    color: CLIColorModeLiteral | None = None,
) -> None:
    """Entrypoint for ``tmuxp edit``, open tmuxp workspace file in system editor."""
    color_mode = get_color_mode(color)
    colors = Colors(color_mode)

    workspace_file = find_workspace_file(workspace_file)

    sys_editor = os.environ.get("EDITOR", "vim")
    print(  # NOQA: T201 RUF100
        colors.muted("Opening ")
        + colors.info(str(PrivatePath(workspace_file)))
        + colors.muted(" in ")
        + colors.highlight(sys_editor, bold=False)
        + colors.muted("..."),
    )
    subprocess.call([sys_editor, workspace_file])
