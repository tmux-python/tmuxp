"""CLI for ``tmuxp copy`` subcommand."""

from __future__ import annotations

import logging
import os
import shutil
import typing as t

from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace.finders import find_workspace_file, get_workspace_dir, is_pure_name

from ._colors import Colors, build_description, get_color_mode
from .utils import prompt_yes_no, tmuxp_echo

logger = logging.getLogger(__name__)

COPY_DESCRIPTION = build_description(
    """
    Copy an existing workspace config to a new name.

    Source is resolved using the same logic as ``tmuxp load`` (supports
    names, paths, and extensions). If destination is a plain name, it
    is placed in the workspace directory as ``<name>.yaml``.
    """,
    (
        (
            None,
            [
                "tmuxp copy myproject myproject-backup",
                "tmuxp copy dev staging",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    import argparse

    CLIColorModeLiteral: t.TypeAlias = t.Literal["auto", "always", "never"]


def create_copy_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``copy`` subcommand.

    Examples
    --------
    >>> import argparse
    >>> parser = create_copy_subparser(argparse.ArgumentParser())
    >>> args = parser.parse_args(["src", "dst"])
    >>> args.source, args.destination
    ('src', 'dst')

    No arguments yields ``None``:

    >>> args = parser.parse_args([])
    >>> args.source is None and args.destination is None
    True
    """
    parser.add_argument(
        dest="source",
        metavar="source",
        nargs="?",
        default=None,
        type=str,
        help="source workspace name or file path.",
    )
    parser.add_argument(
        dest="destination",
        metavar="destination",
        nargs="?",
        default=None,
        type=str,
        help="destination workspace name or file path.",
    )
    parser.set_defaults(print_help=parser.print_help)
    return parser


def command_copy(
    source: str,
    destination: str,
    parser: argparse.ArgumentParser | None = None,
    color: CLIColorModeLiteral | None = None,
) -> None:
    r"""Entrypoint for ``tmuxp copy``, copy a workspace config to a new name.

    Examples
    --------
    >>> monkeypatch.setenv("TMUXP_CONFIGDIR", str(tmp_path))
    >>> _ = (tmp_path / "src.yaml").write_text(
    ...     "session_name: s\nwindows:\n  - window_name: m\n    panes:\n      -\n"
    ... )
    >>> command_copy("src", "dst", color="never")  # doctest: +ELLIPSIS
    Copied ...src.yaml ... ...dst.yaml
    >>> (tmp_path / "dst.yaml").exists()
    True
    """
    color_mode = get_color_mode(color)
    colors = Colors(color_mode)

    try:
        source_path = find_workspace_file(source)
    except FileNotFoundError:
        tmuxp_echo(colors.error(f"Source not found: {source}"))
        return

    if is_pure_name(destination):
        workspace_dir = get_workspace_dir()
        os.makedirs(workspace_dir, exist_ok=True)
        dest_path = os.path.join(workspace_dir, f"{destination}.yaml")
    else:
        dest_path = os.path.expanduser(destination)
        if not os.path.isabs(dest_path):
            dest_path = os.path.normpath(os.path.join(os.getcwd(), dest_path))

    if os.path.exists(dest_path) and not prompt_yes_no(
        f"Overwrite {colors.info(str(PrivatePath(dest_path)))}?",
        default=False,
        color_mode=color_mode,
    ):
        tmuxp_echo(colors.muted("Aborted."))
        return

    shutil.copy2(source_path, dest_path)
    tmuxp_echo(
        colors.success("Copied ")
        + colors.info(str(PrivatePath(source_path)))
        + colors.muted(" \u2192 ")
        + colors.info(str(PrivatePath(dest_path))),
    )
