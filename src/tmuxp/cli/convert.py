"""CLI for ``tmuxp convert`` subcommand."""
import argparse
import os
import pathlib
import typing as t

from tmuxp._internal.config_reader import ConfigReader
from tmuxp.workspace.finders import find_workspace_file, get_workspace_dir

from .. import exc
from .utils import prompt_yes_no

if t.TYPE_CHECKING:
    AllowedFileTypes = t.Literal["json", "yaml"]


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
    workspace_file: t.Union[str, pathlib.Path],
    answer_yes: bool,
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
    """Entrypoint for ``tmuxp convert`` convert a tmuxp config between JSON and YAML."""
    workspace_file = find_workspace_file(
        workspace_file,
        workspace_dir=get_workspace_dir(),
    )

    if isinstance(workspace_file, str):
        workspace_file = pathlib.Path(workspace_file)

    _, ext = os.path.splitext(workspace_file)
    ext = ext.lower()
    to_filetype: "AllowedFileTypes"
    if ext == ".json":
        to_filetype = "yaml"
    elif ext in [".yaml", ".yml"]:
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
        and prompt_yes_no(f"Convert to <{workspace_file}> to {to_filetype}?")
        and prompt_yes_no("Save workspace to %s?" % newfile)
    ):
        answer_yes = True

    if answer_yes:
        with open(newfile, "w") as buf:
            buf.write(new_workspace)
        print(f"New workspace file saved to <{newfile}>.")
