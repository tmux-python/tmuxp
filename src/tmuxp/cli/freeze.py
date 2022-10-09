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
from .utils import get_config_dir, prompt, prompt_choices, prompt_yes_no

if t.TYPE_CHECKING:
    from typing_extensions import Literal, TypeAlias, TypeGuard

    CLIOutputFormatLiteral: TypeAlias = Literal["yaml", "json"]


class CLIFreezeNamespace(argparse.Namespace):
    session_name: str
    socket_name: t.Optional[str]
    socket_path: t.Optional[str]
    config_format: t.Optional["CLIOutputFormatLiteral"]
    save_to: t.Optional[str]
    answer_yes: t.Optional[bool]
    quiet: t.Optional[bool]
    force: t.Optional[bool]


def session_completion(ctx, params, incomplete):
    server = Server()
    choices = [session.name for session in server.list_sessions()]
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
    args: CLIFreezeNamespace,
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
    """Snapshot a session into a config.

    If SESSION_NAME is provided, snapshot that session. Otherwise, use the
    current session."""
    server = Server(socket_name=args.socket_name, socket_path=args.socket_path)

    try:
        if args.session_name:
            session = server.find_where({"session_name": args.session_name})
        else:
            session = util.get_session(server)

        if not session:
            raise TmuxpException("Session not found.")
    except TmuxpException as e:
        print(e)
        return

    sconf = freeze(session)
    newconfig = config.inline(sconf)
    configparser = ConfigReader(newconfig)

    if not args.quiet:
        print(
            "---------------------------------------------------------------"
            "\n"
            "Freeze does its best to snapshot live tmux sessions.\n"
        )
    if not (
        args.answer_yes
        or prompt_yes_no(
            "The new config *WILL* require adjusting afterwards. Save config?"
        )
    ):
        if not args.quiet:
            print(
                "tmuxp has examples in JSON and YAML format at "
                "<http://tmuxp.git-pull.com/examples.html>\n"
                "View tmuxp docs at <http://tmuxp.git-pull.com/>."
            )
        sys.exit()

    dest = args.save_to
    while not dest:
        save_to = os.path.abspath(
            os.path.join(
                get_config_dir(),
                "{}.{}".format(sconf.get("session_name"), args.config_format or "yaml"),
            )
        )
        dest_prompt = prompt(
            "Save to: %s" % save_to,
            default=save_to,
        )
        if not args.force and os.path.exists(dest_prompt):
            print("%s exists. Pick a new filename." % dest_prompt)
            continue

        dest = dest_prompt
    dest = os.path.abspath(os.path.relpath(os.path.expanduser(dest)))
    config_format = args.config_format

    valid_config_formats: t.List["CLIOutputFormatLiteral"] = ["json", "yaml"]

    def is_valid_ext(stem: t.Optional[str]) -> "TypeGuard[CLIOutputFormatLiteral]":
        return stem in valid_config_formats

    if not is_valid_ext(config_format):

        def extract_config_format(val: str) -> t.Optional["CLIOutputFormatLiteral"]:
            suffix = pathlib.Path(val).suffix
            if isinstance(suffix, str):
                suffix = suffix.lower().lstrip(".")
                if is_valid_ext(suffix):
                    return suffix
            return None

        config_format = extract_config_format(dest)
        if not is_valid_ext(config_format):
            config_format = prompt_choices(
                "Couldn't ascertain one of [%s] from file name. Convert to"
                % ", ".join(valid_config_formats),
                choices=valid_config_formats,
                default="yaml",
            )

    if config_format == "yaml":
        newconfig = configparser.dump(
            format="yaml", indent=2, default_flow_style=False, safe=True
        )
    elif config_format == "json":
        newconfig = configparser.dump(format="json", indent=2)

    if args.answer_yes or prompt_yes_no("Save to %s?" % dest):
        destdir = os.path.dirname(dest)
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        buf = open(dest, "w")
        buf.write(newconfig)
        buf.close()

        if not args.quiet:
            print("Saved to %s." % dest)
