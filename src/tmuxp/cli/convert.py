import argparse
import os
import pathlib
import typing as t

from tmuxp.config_reader import ConfigReader
from tmuxp.workspace.finders import find_workspace_file, get_workspace_dir

from .utils import prompt_yes_no


def create_convert_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
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


def command_convert(
    workspace_file: t.Union[str, pathlib.Path],
    answer_yes: bool,
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
    """Convert a tmuxp config between JSON and YAML."""
    workspace_file = find_workspace_file(
        workspace_file, workspace_dir=get_workspace_dir()
    )

    if isinstance(workspace_file, str):
        workspace_file = pathlib.Path(workspace_file)

    _, ext = os.path.splitext(workspace_file)
    ext = ext.lower()
    if ext == ".json":
        to_filetype = "yaml"
    elif ext in [".yaml", ".yml"]:
        to_filetype = "json"
    else:
        raise Exception(f"Unknown filetype: {ext} (valid: [.json, .yaml, .yml])")

    configparser = ConfigReader.from_file(workspace_file)
    newfile = workspace_file.parent / (str(workspace_file.stem) + f".{to_filetype}")

    export_kwargs = {"default_flow_style": False} if to_filetype == "yaml" else {}
    new_workspace = configparser.dump(format=to_filetype, indent=2, **export_kwargs)

    if not answer_yes:
        if prompt_yes_no(f"Convert to <{workspace_file}> to {to_filetype}?"):
            if prompt_yes_no("Save workspace to %s?" % newfile):
                answer_yes = True

    if answer_yes:
        buf = open(newfile, "w")
        buf.write(new_workspace)
        buf.close()
        print(f"New workspace file saved to <{newfile}>.")
