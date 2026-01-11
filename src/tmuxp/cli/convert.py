"""CLI for ``tmuxp convert`` subcommand."""

from __future__ import annotations

import locale
import os
import pathlib
import typing as t

from tmuxp import exc
from tmuxp._internal.config_reader import ConfigReader
from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace.finders import find_workspace_file, get_workspace_dir

from ._colors import Colors, build_description, get_color_mode
from .utils import prompt_yes_no

CONVERT_DESCRIPTION = build_description(
    """
    Convert workspace files between YAML and JSON format.
    """,
    (
        (
            None,
            [
                "tmuxp convert workspace.yaml",
                "tmuxp convert workspace.json",
                "tmuxp convert -y workspace.yaml",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    import argparse

    AllowedFileTypes = t.Literal["json", "yaml"]
    CLIColorModeLiteral: t.TypeAlias = t.Literal["auto", "always", "never"]


def create_convert_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``convert`` subcommand."""
    workspace_file = parser.add_argument(
        dest="workspace_file",
        type=str,
        metavar="workspace-file",
        help="checks tmuxp and current directory for workspace files.",
    )
    try:
        import shtab

        workspace_file.complete = shtab.FILE  # type: ignore
    except ImportError:
        pass

    parser.add_argument(
        "--yes",
        "-y",
        dest="answer_yes",
        action="store_true",
        help="always answer yes",
    )
    return parser


class ConvertUnknownFileType(exc.TmuxpException):
    """Raise if tmuxp convert encounters an unknown filetype."""

    def __init__(self, ext: str, *args: object, **kwargs: object) -> None:
        return super().__init__(
            f"Unknown filetype: {ext} (valid: [.json, .yaml, .yml])",
        )


def command_convert(
    workspace_file: str | pathlib.Path,
    answer_yes: bool,
    parser: argparse.ArgumentParser | None = None,
    color: CLIColorModeLiteral | None = None,
) -> None:
    """Entrypoint for ``tmuxp convert`` convert a tmuxp config between JSON and YAML."""
    color_mode = get_color_mode(color)
    colors = Colors(color_mode)

    workspace_file = find_workspace_file(
        workspace_file,
        workspace_dir=get_workspace_dir(),
    )

    if isinstance(workspace_file, str):
        workspace_file = pathlib.Path(workspace_file)

    _, ext = os.path.splitext(workspace_file)
    ext = ext.lower()
    to_filetype: AllowedFileTypes
    if ext == ".json":
        to_filetype = "yaml"
    elif ext in {".yaml", ".yml"}:
        to_filetype = "json"
    else:
        raise ConvertUnknownFileType(ext)

    configparser = ConfigReader.from_file(workspace_file)
    newfile = workspace_file.parent / (str(workspace_file.stem) + f".{to_filetype}")

    new_workspace = configparser.dump(
        fmt=to_filetype,
        indent=2,
        **{"default_flow_style": False} if to_filetype == "yaml" else {},
    )

    if (
        not answer_yes
        and prompt_yes_no(
            f"Convert {colors.info(str(PrivatePath(workspace_file)))} to "
            f"{colors.highlight(to_filetype)}?",
            color_mode=color_mode,
        )
        and prompt_yes_no(
            f"Save workspace to {colors.info(str(PrivatePath(newfile)))}?",
            color_mode=color_mode,
        )
    ):
        answer_yes = True

    if answer_yes:
        pathlib.Path(newfile).write_text(
            new_workspace,
            encoding=locale.getpreferredencoding(False),
        )
        print(  # NOQA: T201 RUF100
            colors.success("New workspace file saved to ")
            + colors.info(str(PrivatePath(newfile)))
            + ".",
        )
