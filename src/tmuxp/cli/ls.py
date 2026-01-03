"""CLI for ``tmuxp ls`` subcommand."""

from __future__ import annotations

import argparse
import os
import typing as t

from tmuxp.workspace.constants import VALID_WORKSPACE_DIR_FILE_EXTENSIONS
from tmuxp.workspace.finders import get_workspace_dir

from ._colors import Colors, get_color_mode

if t.TYPE_CHECKING:
    from typing import TypeAlias

    CLIColorModeLiteral: TypeAlias = t.Literal["auto", "always", "never"]


class CLILsNamespace(argparse.Namespace):
    """Typed :class:`argparse.Namespace` for tmuxp ls command."""

    color: CLIColorModeLiteral


def create_ls_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``ls`` subcommand."""
    return parser


def command_ls(
    args: CLILsNamespace | None = None,
    parser: argparse.ArgumentParser | None = None,
) -> None:
    """Entrypoint for ``tmuxp ls`` subcommand."""
    # Get color mode from args or default to AUTO
    color_mode = get_color_mode(args.color if args else None)
    colors = Colors(color_mode)

    tmuxp_dir = get_workspace_dir()
    if os.path.exists(tmuxp_dir) and os.path.isdir(tmuxp_dir):
        for f in sorted(os.listdir(tmuxp_dir)):
            stem, ext = os.path.splitext(f)
            if os.path.isdir(f) or ext not in VALID_WORKSPACE_DIR_FILE_EXTENSIONS:
                continue
            print(colors.info(stem))  # NOQA: T201 RUF100
