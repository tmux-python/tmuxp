import argparse
import os
import pathlib
import typing as t

from tmuxp.config_reader import ConfigReader

from .utils import get_config_dir, prompt_yes_no, scan_config


def create_convert_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    workspace_file = parser.add_argument(
        dest="workspace_file",
        type=str,
        metavar="config-file",
        help="checks tmuxp and current directory for config files.",
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
    workspace_file = scan_config(workspace_file, config_dir=get_config_dir())

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
    new_config = configparser.dump(format=to_filetype, indent=2, **export_kwargs)

    if not answer_yes:
        if prompt_yes_no(f"Convert to <{workspace_file}> to {to_filetype}?"):
            if prompt_yes_no("Save config to %s?" % newfile):
                answer_yes = True

    if answer_yes:
        buf = open(newfile, "w")
        buf.write(new_config)
        buf.close()
        print(f"New config saved to <{newfile}>.")
