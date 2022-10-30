import argparse
import os
import pathlib
import sys
import typing as t

from tmuxp.config_reader import ConfigReader
from tmuxp.workspace.finders import find_workspace_file

from ..workspace import importers
from .utils import prompt, prompt_choices, prompt_yes_no, tmuxp_echo


def get_tmuxinator_dir() -> str:
    """
    Return tmuxinator configuration directory.

    Checks for ``TMUXINATOR_CONFIG`` environmental variable.

    Returns
    -------
    str :
        absolute path to tmuxinator config directory

    See Also
    --------
    :meth:`tmuxp.workspace.importers.tmuxinator.import_tmuxinator`
    """
    if "TMUXINATOR_CONFIG" in os.environ:
        return os.path.expanduser(os.environ["TMUXINATOR_CONFIG"])

    return os.path.expanduser("~/.tmuxinator/")


def get_teamocil_dir() -> str:
    """
    Return teamocil configuration directory.

    Returns
    -------
    str :
        absolute path to teamocil config directory

    See Also
    --------
    :meth:`tmuxp.workspace.importers.teamocil.import_teamocil`
    """
    return os.path.expanduser("~/.teamocil/")


def _resolve_path_no_overwrite(workspace_file: str) -> str:
    path = pathlib.Path(workspace_file).resolve()
    if path.exists():
        raise ValueError("%s exists. Pick a new filename." % path)
    return str(path)


def command_import(
    workspace_file: str,
    print_list: str,
    parser: argparse.ArgumentParser,
):
    """Import a teamocil/tmuxinator config."""


def create_import_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    importsubparser = parser.add_subparsers(
        title="commands", description="valid commands", help="additional help"
    )

    import_teamocil = importsubparser.add_parser(
        "teamocil", help="convert and import a teamocil config"
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
        callback=command_import_teamocil, import_subparser_name="teamocil"
    )

    import_tmuxinator = importsubparser.add_parser(
        "tmuxinator", help="convert and import a tmuxinator config"
    )

    import_tmuxinatorgroup = import_tmuxinator.add_mutually_exclusive_group(
        required=True
    )
    tmuxinator_workspace_file = import_tmuxinatorgroup.add_argument(
        dest="workspace_file",
        type=str,
        nargs="?",
        metavar="workspace-file",
        help="checks current ~/.tmuxinator and current directory for yaml files",
    )

    import_tmuxinator.set_defaults(
        callback=command_import_tmuxinator, import_subparser_name="tmuxinator"
    )

    try:
        import shtab

        teamocil_workspace_file.complete = shtab.FILE  # type: ignore
        tmuxinator_workspace_file.complete = shtab.FILE  # type: ignore
    except ImportError:
        pass

    return parser


def import_config(
    workspace_file: str,
    importfunc: t.Callable,
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
    existing_workspace_file = ConfigReader._from_file(pathlib.Path(workspace_file))
    cfg_reader = ConfigReader(importfunc(existing_workspace_file))

    workspace_file_format = prompt_choices(
        "Convert to", choices=["yaml", "json"], default="yaml"
    )

    if workspace_file_format == "yaml":
        new_config = cfg_reader.dump("yaml", indent=2, default_flow_style=False)
    elif workspace_file_format == "json":
        new_config = cfg_reader.dump("json", indent=2)
    else:
        sys.exit("Unknown config format.")

    tmuxp_echo(
        new_config + "---------------------------------------------------------------"
        "\n"
        "Configuration import does its best to convert files.\n"
    )
    if prompt_yes_no(
        "The new config *WILL* require adjusting afterwards. Save config?"
    ):
        dest = None
        while not dest:
            dest_path = prompt(
                "Save to [%s]" % os.getcwd(), value_proc=_resolve_path_no_overwrite
            )

            # dest = dest_prompt
            if prompt_yes_no("Save to %s?" % dest_path):
                dest = dest_path

        buf = open(dest, "w")
        buf.write(new_config)
        buf.close()

        tmuxp_echo("Saved to %s." % dest)
    else:
        tmuxp_echo(
            "tmuxp has examples in JSON and YAML format at "
            "<http://tmuxp.git-pull.com/examples.html>\n"
            "View tmuxp docs at <http://tmuxp.git-pull.com/>"
        )
        sys.exit()


def command_import_tmuxinator(
    workspace_file: str,
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
    """Convert a tmuxinator config from workspace_file to tmuxp format and import
    it into tmuxp."""
    workspace_file = find_workspace_file(
        workspace_file, workspace_dir=get_tmuxinator_dir()
    )
    import_config(workspace_file, importers.import_tmuxinator)


def command_import_teamocil(
    workspace_file: str,
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
    """Convert a teamocil config from workspace_file to tmuxp format and import
    it into tmuxp."""
    workspace_file = find_workspace_file(
        workspace_file, workspace_dir=get_teamocil_dir()
    )

    import_config(workspace_file, importers.import_teamocil)
