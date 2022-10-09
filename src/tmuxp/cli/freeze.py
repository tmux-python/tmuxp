import argparse
import os
import pathlib
import sys
import typing as t

from libtmux.server import Server
from tmuxp.config_reader import ConfigReader
from tmuxp.exc import TmuxpException

from .. import config, util
from ..workspacebuilder import freeze
from .utils import _validate_choices, get_config_dir, prompt, prompt_yes_no


def session_completion(ctx, params, incomplete):
    t = Server()
    choices = [session.name for session in t.list_sessions()]
    return sorted(str(c) for c in choices if str(c).startswith(incomplete))


def create_freeze_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    parser.add_argument(
        dest="session_name",
        metavar="session-name",
        nargs="?",
        action="store",
    )
    parser.add_argument(
        "-S", dest="socket_path", metavar="socket-path", help="pass-through for tmux -S"
    )
    parser.add_argument(
        "-L", dest="socket_name", metavar="socket-name", help="pass-through for tmux -L"
    )
    parser.add_argument(
        "-f",
        "--config-format",
        choices=["yaml", "json"],
        help="format to save in",
    )
    parser.add_argument(
        "-o",
        "--save-to",
        metavar="output-path",
        type=pathlib.Path,
        help="file to save to",
    )
    parser.add_argument(
        "--yes",
        "-y",
        dest="answer_yes",
        action="store_true",
        help="always answer yes",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        dest="quiet",
        action="store_true",
        help="don't prompt for confirmation",
    )
    parser.add_argument(
        "--force", dest="force", action="store_true", help="overwrite the config file"
    )

    return parser


def command_freeze(
    session_name: t.Optional[str] = None,
    socket_name: t.Optional[str] = None,
    config_format: t.Optional[str] = None,
    save_to: t.Optional[str] = None,
    socket_path: t.Optional[str] = None,
    answer_yes: t.Optional[bool] = None,
    quiet: t.Optional[bool] = None,
    force: t.Optional[bool] = None,
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
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
        answer_yes
        or prompt_yes_no(
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
        dest_prompt = prompt(
            "Save to: %s" % save_to,
            default=save_to,
        )
        if not force and os.path.exists(dest_prompt):
            print("%s exists. Pick a new filename." % dest_prompt)
            continue

        dest = dest_prompt
    dest = os.path.abspath(os.path.relpath(os.path.expanduser(dest)))

    if config_format is None or config_format == "":
        valid_config_formats = ["json", "yaml"]
        _, config_format = os.path.splitext(dest)
        config_format = config_format[1:].lower()
        if config_format not in valid_config_formats:
            config_format = prompt(
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

    if answer_yes or prompt_yes_no("Save to %s?" % dest):
        destdir = os.path.dirname(dest)
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        buf = open(dest, "w")
        buf.write(newconfig)
        buf.close()

        if not quiet:
            print("Saved to %s." % dest)
