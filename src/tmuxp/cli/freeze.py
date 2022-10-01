import os
import sys

import click

from libtmux.server import Server
from tmuxp.config_reader import ConfigReader
from tmuxp.exc import TmuxpException

from .. import config, util
from ..workspacebuilder import freeze
from .utils import _validate_choices, get_abs_path, get_config_dir


def session_completion(ctx, params, incomplete):
    t = Server()
    choices = [session.name for session in t.list_sessions()]
    return sorted(str(c) for c in choices if str(c).startswith(incomplete))


@click.command(name="freeze")
@click.argument(
    "session_name", nargs=1, required=False, shell_complete=session_completion
)
@click.option("-S", "socket_path", help="pass-through for tmux -S")
@click.option("-L", "socket_name", help="pass-through for tmux -L")
@click.option(
    "-f",
    "--config-format",
    type=click.Choice(["yaml", "json"]),
    help="format to save in",
)
@click.option("-o", "--save-to", type=click.Path(exists=False), help="file to save to")
@click.option(
    "-y",
    "--yes",
    type=bool,
    is_flag=True,
    default=False,
    help="Don't prompt for confirmation",
)
@click.option(
    "-q",
    "--quiet",
    type=bool,
    is_flag=True,
    default=False,
    help="Don't prompt for confirmation",
)
@click.option("--force", "force", help="overwrite the config file", is_flag=True)
def command_freeze(
    session_name, socket_name, config_format, save_to, socket_path, yes, quiet, force
):
    """Snapshot a session into a config.

    If SESSION_NAME is provided, snapshot that session. Otherwise, use the
    current session."""

    t = Server(socket_name=socket_name, socket_path=socket_path)

    try:
        if session_name:
            session = t.find_where({"session_name": session_name})
        else:
            session = util.get_session(t)

        if not session:
            raise TmuxpException("Session not found.")
    except TmuxpException as e:
        print(e)
        return

    sconf = freeze(session)
    newconfig = config.inline(sconf)
    configparser = ConfigReader(newconfig)

    if not quiet:
        print(
            "---------------------------------------------------------------"
            "\n"
            "Freeze does its best to snapshot live tmux sessions.\n"
        )
    if not (
        yes
        or click.confirm(
            "The new config *WILL* require adjusting afterwards. Save config?"
        )
    ):
        if not quiet:
            print(
                "tmuxp has examples in JSON and YAML format at "
                "<http://tmuxp.git-pull.com/examples.html>\n"
                "View tmuxp docs at <http://tmuxp.git-pull.com/>."
            )
        sys.exit()

    dest = save_to
    while not dest:
        save_to = os.path.abspath(
            os.path.join(
                get_config_dir(),
                "{}.{}".format(sconf.get("session_name"), config_format or "yaml"),
            )
        )
        dest_prompt = click.prompt(
            "Save to: %s" % save_to, value_proc=get_abs_path, default=save_to
        )
        if not force and os.path.exists(dest_prompt):
            print("%s exists. Pick a new filename." % dest_prompt)
            continue

        dest = dest_prompt
    dest = os.path.abspath(os.path.relpath(os.path.expanduser(dest)))

    if config_format is None:
        valid_config_formats = ["json", "yaml"]
        _, config_format = os.path.splitext(dest)
        config_format = config_format[1:].lower()
        if config_format not in valid_config_formats:
            config_format = click.prompt(
                "Couldn't ascertain one of [%s] from file name. Convert to"
                % ", ".join(valid_config_formats),
                value_proc=_validate_choices(["yaml", "json"]),
                default="yaml",
            )

    if config_format == "yaml":
        newconfig = configparser.dump(
            format="yaml", indent=2, default_flow_style=False, safe=True
        )
    elif config_format == "json":
        newconfig = configparser.dump(format="json", indent=2)

    if yes or click.confirm("Save to %s?" % dest):
        destdir = os.path.dirname(dest)
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        buf = open(dest, "w")
        buf.write(newconfig)
        buf.close()

        if not quiet:
            print("Saved to %s." % dest)
