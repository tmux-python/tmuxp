"""CLI for ``tmuxp import`` subcommand."""

from __future__ import annotations

import locale
import os
import pathlib
import sys
import typing as t

from tmuxp._internal.config_reader import ConfigReader
from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace import importers
from tmuxp.workspace.finders import find_workspace_file

from ._colors import ColorMode, Colors, build_description, get_color_mode
from .utils import prompt, prompt_choices, prompt_yes_no, tmuxp_echo

IMPORT_DESCRIPTION = build_description(
    """
    Import workspaces from teamocil and tmuxinator configuration files.
    """,
    (
        (
            "teamocil",
            [
                "tmuxp import teamocil ~/.teamocil/project.yml",
            ],
        ),
        (
            "tmuxinator",
            [
                "tmuxp import tmuxinator ~/.tmuxinator/project.yml",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    import argparse
    from typing import TypeAlias

    CLIColorModeLiteral: TypeAlias = t.Literal["auto", "always", "never"]


def get_tmuxinator_dir() -> pathlib.Path:
    """Return tmuxinator configuration directory.

    Checks for ``TMUXINATOR_CONFIG`` environmental variable.

    Returns
    -------
    pathlib.Path :
        absolute path to tmuxinator config directory

    See Also
    --------
    :meth:`tmuxp.workspace.importers.import_tmuxinator`
    """
    if "TMUXINATOR_CONFIG" in os.environ:
        return pathlib.Path(os.environ["TMUXINATOR_CONFIG"]).expanduser()

    return pathlib.Path("~/.tmuxinator/").expanduser()


def get_teamocil_dir() -> pathlib.Path:
    """Return teamocil configuration directory.

    Returns
    -------
    pathlib.Path :
        absolute path to teamocil config directory

    See Also
    --------
    :meth:`tmuxp.workspace.importers.import_teamocil`
    """
    return pathlib.Path("~/.teamocil/").expanduser()


def _resolve_path_no_overwrite(workspace_file: str) -> str:
    path = pathlib.Path(workspace_file).resolve()
    if path.exists():
        msg = f"{path} exists. Pick a new filename."
        raise ValueError(msg)
    return str(path)


def command_import(
    workspace_file: str,
    print_list: str,
    parser: argparse.ArgumentParser,
) -> None:
    """Import a teamocil/tmuxinator config."""


def create_import_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``import`` subparser."""
    importsubparser = parser.add_subparsers(
        title="commands",
        description="valid commands",
        help="additional help",
    )

    import_teamocil = importsubparser.add_parser(
        "teamocil",
        help="convert and import a teamocil config",
    )

    import_teamocilgroup = import_teamocil.add_mutually_exclusive_group(required=True)
    teamocil_workspace_file = import_teamocilgroup.add_argument(
        dest="workspace_file",
        type=str,
        nargs="?",
        metavar="workspace-file",
        help="checks current ~/.teamocil and current directory for yaml files",
    )
    import_teamocil.set_defaults(
        callback=command_import_teamocil,
        import_subparser_name="teamocil",
    )

    import_tmuxinator = importsubparser.add_parser(
        "tmuxinator",
        help="convert and import a tmuxinator config",
    )

    import_tmuxinatorgroup = import_tmuxinator.add_mutually_exclusive_group(
        required=True,
    )
    tmuxinator_workspace_file = import_tmuxinatorgroup.add_argument(
        dest="workspace_file",
        type=str,
        nargs="?",
        metavar="workspace-file",
        help="checks current ~/.tmuxinator and current directory for yaml files",
    )

    import_tmuxinator.set_defaults(
        callback=command_import_tmuxinator,
        import_subparser_name="tmuxinator",
    )

    try:
        import shtab

        teamocil_workspace_file.complete = shtab.FILE  # type: ignore
        tmuxinator_workspace_file.complete = shtab.FILE  # type: ignore
    except ImportError:
        pass

    return parser


class ImportConfigFn(t.Protocol):
    """Typing for import configuration callback function."""

    def __call__(self, workspace_dict: dict[str, t.Any]) -> dict[str, t.Any]:
        """Execute tmuxp import function."""
        ...


def import_config(
    workspace_file: str,
    importfunc: ImportConfigFn,
    parser: argparse.ArgumentParser | None = None,
    colors: Colors | None = None,
) -> None:
    """Import a configuration from a workspace_file."""
    if colors is None:
        colors = Colors(ColorMode.AUTO)

    existing_workspace_file = ConfigReader._from_file(pathlib.Path(workspace_file))
    cfg_reader = ConfigReader(importfunc(existing_workspace_file))

    workspace_file_format = prompt_choices(
        "Convert to",
        choices=["yaml", "json"],
        default="yaml",
        color_mode=colors.mode,
    )

    if workspace_file_format == "yaml":
        new_config = cfg_reader.dump("yaml", indent=2, default_flow_style=False)
    elif workspace_file_format == "json":
        new_config = cfg_reader.dump("json", indent=2)
    else:
        sys.exit(colors.error("Unknown config format."))

    tmuxp_echo(
        new_config
        + colors.format_separator(63)
        + "\n"
        + colors.muted("Configuration import does its best to convert files.")
        + "\n",
    )
    if prompt_yes_no(
        "The new config *WILL* require adjusting afterwards. Save config?",
        color_mode=colors.mode,
    ):
        dest = None
        while not dest:
            dest_path = prompt(
                f"Save to [{PrivatePath(os.getcwd())}]",
                value_proc=_resolve_path_no_overwrite,
                color_mode=colors.mode,
            )

            # dest = dest_prompt
            if prompt_yes_no(
                f"Save to {PrivatePath(dest_path)}?",
                color_mode=colors.mode,
            ):
                dest = dest_path

        pathlib.Path(dest).write_text(
            new_config,
            encoding=locale.getpreferredencoding(False),
        )

        tmuxp_echo(
            colors.success("Saved to ") + colors.info(str(PrivatePath(dest))) + ".",
        )
    else:
        tmuxp_echo(
            colors.muted("tmuxp has examples in JSON and YAML format at ")
            + colors.info("<http://tmuxp.git-pull.com/examples.html>")
            + "\n"
            + colors.muted("View tmuxp docs at ")
            + colors.info("<http://tmuxp.git-pull.com/>"),
        )
        sys.exit()


def command_import_tmuxinator(
    workspace_file: str,
    parser: argparse.ArgumentParser | None = None,
    color: CLIColorModeLiteral | None = None,
) -> None:
    """Entrypoint for ``tmuxp import tmuxinator`` subcommand.

    Converts a tmuxinator config from workspace_file to tmuxp format and import
    it into tmuxp.
    """
    color_mode = get_color_mode(color)
    colors = Colors(color_mode)

    workspace_file = find_workspace_file(
        workspace_file,
        workspace_dir=get_tmuxinator_dir(),
    )
    import_config(workspace_file, importers.import_tmuxinator, colors=colors)


def command_import_teamocil(
    workspace_file: str,
    parser: argparse.ArgumentParser | None = None,
    color: CLIColorModeLiteral | None = None,
) -> None:
    """Entrypoint for ``tmuxp import teamocil`` subcommand.

    Convert a teamocil config from workspace_file to tmuxp format and import
    it into tmuxp.
    """
    color_mode = get_color_mode(color)
    colors = Colors(color_mode)

    workspace_file = find_workspace_file(
        workspace_file,
        workspace_dir=get_teamocil_dir(),
    )

    import_config(workspace_file, importers.import_teamocil, colors=colors)
