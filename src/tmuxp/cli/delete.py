"""CLI for ``tmuxp delete`` subcommand."""

from __future__ import annotations

import logging
import os
import typing as t

from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace.finders import find_workspace_file

from ._colors import Colors, build_description, get_color_mode
from .utils import prompt_yes_no, tmuxp_echo

logger = logging.getLogger(__name__)

DELETE_DESCRIPTION = build_description(
    """
    Delete workspace config files.

    Resolves workspace names using the same logic as ``tmuxp load``.
    Prompts for confirmation unless ``-y`` is passed.
    """,
    (
        (
            None,
            [
                "tmuxp delete myproject",
                "tmuxp delete -y old-project",
                "tmuxp delete proj1 proj2",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    import argparse

    CLIColorModeLiteral: t.TypeAlias = t.Literal["auto", "always", "never"]


def create_delete_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``delete`` subcommand.

    Examples
    --------
    >>> import argparse
    >>> parser = create_delete_subparser(argparse.ArgumentParser())
    >>> args = parser.parse_args(["proj1", "proj2", "-y"])
    >>> args.workspace_names
    ['proj1', 'proj2']
    >>> args.answer_yes
    True
    """
    parser.add_argument(
        dest="workspace_names",
        metavar="workspace-name",
        nargs="+",
        type=str,
        help="workspace name(s) or file path(s) to delete.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        dest="answer_yes",
        action="store_true",
        help="skip confirmation prompt.",
    )
    return parser


def command_delete(
    workspace_names: list[str],
    answer_yes: bool = False,
    parser: argparse.ArgumentParser | None = None,
    color: CLIColorModeLiteral | None = None,
) -> None:
    """Entrypoint for ``tmuxp delete``, remove workspace config files."""
    color_mode = get_color_mode(color)
    colors = Colors(color_mode)

    for name in workspace_names:
        try:
            workspace_path = find_workspace_file(name)
        except FileNotFoundError:
            tmuxp_echo(colors.warning(f"Workspace not found: {name}"))
            continue

        if not answer_yes and not prompt_yes_no(
            f"Delete {colors.info(str(PrivatePath(workspace_path)))}?",
            default=False,
            color_mode=color_mode,
        ):
            tmuxp_echo(colors.muted("Skipped ") + colors.info(name))
            continue

        os.remove(workspace_path)
        tmuxp_echo(
            colors.success("Deleted ") + colors.info(str(PrivatePath(workspace_path))),
        )
