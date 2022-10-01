import os
import pathlib
import sys

import click

from tmuxp.config_reader import ConfigReader

from .. import config
from .utils import ConfigPath, _validate_choices, get_abs_path, tmuxp_echo


def get_tmuxinator_dir():
    """
    Return tmuxinator configuration directory.

    Checks for ``TMUXINATOR_CONFIG`` environmental variable.

    Returns
    -------
    str :
        absolute path to tmuxinator config directory

    See Also
    --------
    :meth:`tmuxp.config.import_tmuxinator`
    """
    if "TMUXINATOR_CONFIG" in os.environ:
        return os.path.expanduser(os.environ["TMUXINATOR_CONFIG"])

    return os.path.expanduser("~/.tmuxinator/")


def get_teamocil_dir():
    """
    Return teamocil configuration directory.

    Returns
    -------
    str :
        absolute path to teamocil config directory

    See Also
    --------
    :meth:`tmuxp.config.import_teamocil`
    """
    return os.path.expanduser("~/.teamocil/")


def _resolve_path_no_overwrite(config):
    path = get_abs_path(config)
    if os.path.exists(path):
        raise click.exceptions.UsageError("%s exists. Pick a new filename." % path)
    return path


@click.group(name="import")
def command_import():
    """Import a teamocil/tmuxinator config."""


def import_config(configfile, importfunc):
    existing_config = ConfigReader._from_file(pathlib.Path(configfile))
    new_config = ConfigReader(importfunc(existing_config))

    config_format = click.prompt(
        "Convert to", value_proc=_validate_choices(["yaml", "json"]), default="yaml"
    )

    if config_format == "yaml":
        new_config = new_config.dump("yaml", indent=2, default_flow_style=False)
    elif config_format == "json":
        new_config = new_config.dump("json", indent=2)
    else:
        sys.exit("Unknown config format.")

    tmuxp_echo(
        new_config + "---------------------------------------------------------------"
        "\n"
        "Configuration import does its best to convert files.\n"
    )
    if click.confirm(
        "The new config *WILL* require adjusting afterwards. Save config?"
    ):
        dest = None
        while not dest:
            dest_path = click.prompt(
                "Save to [%s]" % os.getcwd(), value_proc=_resolve_path_no_overwrite
            )

            # dest = dest_prompt
            if click.confirm("Save to %s?" % dest_path):
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


@command_import.command(
    name="tmuxinator", short_help="Convert and import a tmuxinator config."
)
@click.argument(
    "configfile", type=ConfigPath(exists=True, config_dir=get_tmuxinator_dir), nargs=1
)
def command_import_tmuxinator(configfile):
    """Convert a tmuxinator config from CONFIGFILE to tmuxp format and import
    it into tmuxp."""
    import_config(configfile, config.import_tmuxinator)


@click.command(name="convert")
@click.option(
    "--yes", "-y", "confirmed", help='Auto confirms with "yes".', is_flag=True
)
@click.argument("config", type=ConfigPath(exists=True), nargs=1)
def command_convert(confirmed, config):
    """Convert a tmuxp config between JSON and YAML."""

    _, ext = os.path.splitext(config)
    ext = ext.lower()
    if ext == ".json":
        to_filetype = "yaml"
    elif ext in [".yaml", ".yml"]:
        to_filetype = "json"
    else:
        raise click.BadParameter(
            f"Unknown filetype: {ext} (valid: [.json, .yaml, .yml])"
        )

    configparser = ConfigReader.from_file(config)
    newfile = config.replace(ext, ".%s" % to_filetype)

    export_kwargs = {"default_flow_style": False} if to_filetype == "yaml" else {}
    new_config = configparser.dump(format=to_filetype, indent=2, **export_kwargs)

    if not confirmed:
        if click.confirm(f"convert to <{config}> to {to_filetype}?"):
            if click.confirm("Save config to %s?" % newfile):
                confirmed = True

    if confirmed:
        buf = open(newfile, "w")
        buf.write(new_config)
        buf.close()
        print("New config saved to <%s>." % newfile)


@command_import.command(
    name="teamocil", short_help="Convert and import a teamocil config."
)
@click.argument(
    "configfile", type=ConfigPath(exists=True, config_dir=get_teamocil_dir), nargs=1
)
def command_import_teamocil(configfile):
    """Convert a teamocil config from CONFIGFILE to tmuxp format and import
    it into tmuxp."""

    import_config(configfile, config.import_teamocil)
