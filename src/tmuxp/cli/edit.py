import os
import subprocess

import click

from .utils import ConfigPath, scan_config


@click.command(name="edit", short_help="Run $EDITOR on config.")
@click.argument("config", type=ConfigPath(exists=True), nargs=1)
def command_edit(config):
    config = scan_config(config)

    sys_editor = os.environ.get("EDITOR", "vim")
    subprocess.call([sys_editor, config])
