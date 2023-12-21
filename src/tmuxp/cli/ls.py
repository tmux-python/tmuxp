"""CLI for ``tmuxp ls`` subcommand."""
import argparse
import os
import typing as t

from tmuxp.workspace.constants import VALID_WORKSPACE_DIR_FILE_EXTENSIONS
from tmuxp.workspace.finders import get_workspace_dir


def create_ls_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``ls`` subcommand."""
    return parser


def command_ls(
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
    """Entrypoint for ``tmuxp ls`` subcommand."""
    tmuxp_dir = get_workspace_dir()
    if os.path.exists(tmuxp_dir) and os.path.isdir(tmuxp_dir):
        for f in sorted(os.listdir(tmuxp_dir)):
            stem, ext = os.path.splitext(f)
            if os.path.isdir(f) or ext not in VALID_WORKSPACE_DIR_FILE_EXTENSIONS:
                continue
            print(stem)
