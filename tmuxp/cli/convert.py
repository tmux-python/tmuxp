import os

import click
import kaptan

from .utils import ConfigPath


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

    configparser = kaptan.Kaptan()
    configparser.import_config(config)
    newfile = config.replace(ext, ".%s" % to_filetype)

    export_kwargs = {"default_flow_style": False} if to_filetype == "yaml" else {}
    newconfig = configparser.export(to_filetype, indent=2, **export_kwargs)

    if not confirmed:
        if click.confirm(f"convert to <{config}> to {to_filetype}?"):
            if click.confirm("Save config to %s?" % newfile):
                confirmed = True

    if confirmed:
        buf = open(newfile, "w")
        buf.write(newconfig)
        buf.close()
        print("New config saved to <%s>." % newfile)
