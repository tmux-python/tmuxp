"""CLI for ``tmuxp new`` subcommand."""

from __future__ import annotations

import logging
import os
import subprocess
import typing as t

from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace.finders import get_workspace_dir

from ._colors import Colors, build_description, get_color_mode
from .utils import tmuxp_echo

logger = logging.getLogger(__name__)

WORKSPACE_TEMPLATE = """\
session_name: {name}
windows:
  - window_name: main
    panes:
      -
"""

NEW_DESCRIPTION = build_description(
    """
    Create a new workspace config from a minimal template.

    Opens the new file in $EDITOR after creation. If the workspace
    already exists, opens it for editing.
    """,
    (
        (
            None,
            [
                "tmuxp new myproject",
                "tmuxp new dev-server",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    import argparse

    CLIColorModeLiteral: t.TypeAlias = t.Literal["auto", "always", "never"]


def create_new_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``new`` subcommand.

    Examples
    --------
    >>> import argparse
    >>> parser = create_new_subparser(argparse.ArgumentParser())
    >>> args = parser.parse_args(["myproject"])
    >>> args.workspace_name
    'myproject'
    """
    parser.add_argument(
        dest="workspace_name",
        metavar="workspace-name",
        type=str,
        help="name for the new workspace config.",
    )
    return parser


def command_new(
    workspace_name: str,
    parser: argparse.ArgumentParser | None = None,
    color: CLIColorModeLiteral | None = None,
) -> None:
    """Entrypoint for ``tmuxp new``, create a new workspace config from template."""
    color_mode = get_color_mode(color)
    colors = Colors(color_mode)

    # Use TMUXP_CONFIGDIR directly if set, since get_workspace_dir()
    # only returns it when the directory already exists. The new command
    # needs to create files there even if it doesn't exist yet.
    configdir_env = os.environ.get("TMUXP_CONFIGDIR")
    workspace_dir = (
        os.path.expanduser(configdir_env) if configdir_env else get_workspace_dir()
    )
    os.makedirs(workspace_dir, exist_ok=True)

    workspace_path = os.path.join(workspace_dir, f"{workspace_name}.yaml")

    if os.path.exists(workspace_path):
        tmuxp_echo(
            colors.info(str(PrivatePath(workspace_path)))
            + colors.muted(" already exists, opening in editor."),
        )
    else:
        content = WORKSPACE_TEMPLATE.format(name=workspace_name)
        with open(workspace_path, "w") as f:
            f.write(content)
        tmuxp_echo(
            colors.success("Created ") + colors.info(str(PrivatePath(workspace_path))),
        )

    sys_editor = os.environ.get("EDITOR", "vim")
    subprocess.call([sys_editor, workspace_path])
