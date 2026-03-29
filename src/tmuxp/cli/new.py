"""CLI for ``tmuxp new`` subcommand."""

from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
import sys
import typing as t

from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace.finders import get_workspace_dir

from ._colors import Colors, build_description, get_color_mode
from .utils import tmuxp_echo

logger = logging.getLogger(__name__)

WORKSPACE_TEMPLATE = """\
session_name: '{name}'
windows:
  - window_name: main
    panes:
      -
"""

_YAML_RESERVED_RE = re.compile(
    r"^(true|false|yes|no|on|off|null|~)$",
    re.IGNORECASE,
)


def _validate_workspace_name(name: str) -> str | None:
    """Return error message if name is invalid for a workspace, None if OK.

    Examples
    --------
    >>> from tmuxp.cli.new import _validate_workspace_name
    >>> _validate_workspace_name("myproject") is None
    True
    >>> _validate_workspace_name("../escape") is not None
    True
    >>> _validate_workspace_name("yes") is not None
    True
    >>> _validate_workspace_name("foo'bar") is not None
    True
    """
    if os.sep in name or (os.altsep and os.altsep in name):
        return f"workspace name must not contain path separators: {name!r}"
    if ".." in name:
        return f"workspace name must not contain '..': {name!r}"
    if _YAML_RESERVED_RE.match(name):
        return f"workspace name is a YAML reserved word: {name!r}"
    if name.startswith(("#", "*", "&", "!", "|", ">", "'", '"', "%", "@", "`")):
        return f"workspace name starts with YAML special character: {name!r}"
    if "'" in name or '"' in name:
        return f"workspace name must not contain quotes: {name!r}"
    return None


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

    No arguments yields ``None``:

    >>> args = parser.parse_args([])
    >>> args.workspace_name is None
    True
    """
    parser.add_argument(
        dest="workspace_name",
        metavar="workspace-name",
        nargs="?",
        default=None,
        type=str,
        help="name for the new workspace config.",
    )
    parser.set_defaults(print_help=parser.print_help)
    return parser


def command_new(
    workspace_name: str,
    parser: argparse.ArgumentParser | None = None,
    color: CLIColorModeLiteral | None = None,
) -> None:
    """Entrypoint for ``tmuxp new``, create a new workspace config from template.

    Examples
    --------
    >>> monkeypatch.setenv("TMUXP_CONFIGDIR", str(tmp_path))
    >>> monkeypatch.setenv("EDITOR", "true")
    >>> command_new("myproject", color="never")  # doctest: +ELLIPSIS
    Created ...myproject.yaml
    >>> (tmp_path / "myproject.yaml").exists()
    True
    """
    color_mode = get_color_mode(color)
    colors = Colors(color_mode)

    err = _validate_workspace_name(workspace_name)
    if err:
        tmuxp_echo(colors.error(err))
        sys.exit(1)

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
    try:
        subprocess.call([*shlex.split(sys_editor), workspace_path])
    except FileNotFoundError:
        tmuxp_echo(
            colors.error("Editor not found: ")
            + colors.info(sys_editor)
            + colors.muted(" (set $EDITOR to a valid editor)"),
        )
        sys.exit(1)
