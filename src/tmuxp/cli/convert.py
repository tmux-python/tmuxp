import os
import pathlib

import click

from tmuxp.config_reader import ConfigReader

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

    configparser = ConfigReader.from_file(pathlib.Path(config))
    newfile = config.replace(ext, f".{to_filetype}")

    new_config = configparser.dump(format=to_filetype)

    if not confirmed:
        if click.confirm(f"convert to <{config}> to {to_filetype}?"):
            if click.confirm(f"Save config to {newfile}?"):
                confirmed = True

    if confirmed:
        buf = open(newfile, "w")
        buf.write(new_config)
        buf.close()
        print(f"New config saved to <{newfile}>.")
