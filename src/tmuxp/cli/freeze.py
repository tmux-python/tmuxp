"""CLI for ``tmuxp freeze`` subcommand."""

import argparse
import locale
import os
import pathlib
import sys
import typing as t

from libtmux.server import Server

from tmuxp import exc, util
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.exc import TmuxpException
from tmuxp.workspace import freezer
from tmuxp.workspace.finders import get_workspace_dir

from .utils import prompt, prompt_choices, prompt_yes_no

if t.TYPE_CHECKING:
    from typing_extensions import TypeAlias, TypeGuard

    CLIOutputFormatLiteral: TypeAlias = t.Literal["yaml", "json"]


class CLIFreezeNamespace(argparse.Namespace):
    """Typed :class:`argparse.Namespace` for tmuxp freeze command."""

    session_name: str
    socket_name: t.Optional[str]
    socket_path: t.Optional[str]
    workspace_format: t.Optional["CLIOutputFormatLiteral"]
    save_to: t.Optional[str]
    answer_yes: t.Optional[bool]
    quiet: t.Optional[bool]
    force: t.Optional[bool]


def create_freeze_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``freeze`` subcommand."""
    parser.add_argument(
        dest="session_name",
        metavar="session-name",
        nargs="?",
        action="store",
    )
    parser.add_argument(
        "-S",
        dest="socket_path",
        metavar="socket-path",
        help="pass-through for tmux -S",
    )
    parser.add_argument(
        "-L",
        dest="socket_name",
        metavar="socket-name",
        help="pass-through for tmux -L",
    )
    parser.add_argument(
        "-f",
        "--workspace-format",
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
        "--force",
        dest="force",
        action="store_true",
        help="overwrite the workspace file",
    )

    return parser


def command_freeze(
    args: CLIFreezeNamespace,
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
    """Entrypoint for ``tmuxp freeze``, snapshot a tmux session into a tmuxp workspace.

    If SESSION_NAME is provided, snapshot that session. Otherwise, use the current
    session.
    """
    server = Server(socket_name=args.socket_name, socket_path=args.socket_path)

    try:
        if args.session_name:
            session = server.sessions.get(session_name=args.session_name, default=None)
        else:
            session = util.get_session(server)

        if not session:
            raise exc.SessionNotFound
    except TmuxpException as e:
        print(e)
        return

    frozen_workspace = freezer.freeze(session)
    workspace = freezer.inline(frozen_workspace)
    configparser = ConfigReader(workspace)

    if not args.quiet:
        print(
            "---------------------------------------------------------------"
            "\n"
            "Freeze does its best to snapshot live tmux sessions.\n",
        )
    if not (
        args.answer_yes
        or prompt_yes_no(
            "The new workspace will require adjusting afterwards. Save workspace file?",
        )
    ):
        if not args.quiet:
            print(
                "tmuxp has examples in JSON and YAML format at "
                "<http://tmuxp.git-pull.com/examples.html>\n"
                "View tmuxp docs at <http://tmuxp.git-pull.com/>.",
            )
        sys.exit()

    dest = args.save_to
    while not dest:
        save_to = os.path.abspath(
            os.path.join(
                get_workspace_dir(),
                "{}.{}".format(
                    frozen_workspace.get("session_name"),
                    args.workspace_format or "yaml",
                ),
            ),
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
    workspace_format = args.workspace_format

    valid_workspace_formats: t.List["CLIOutputFormatLiteral"] = ["json", "yaml"]

    def is_valid_ext(stem: t.Optional[str]) -> "TypeGuard[CLIOutputFormatLiteral]":
        return stem in valid_workspace_formats

    if not is_valid_ext(workspace_format):

        def extract_workspace_format(
            val: str,
        ) -> t.Optional["CLIOutputFormatLiteral"]:
            suffix = pathlib.Path(val).suffix
            if isinstance(suffix, str):
                suffix = suffix.lower().lstrip(".")
                if is_valid_ext(suffix):
                    return suffix
            return None

        workspace_format = extract_workspace_format(dest)
        if not is_valid_ext(workspace_format):
            _workspace_format = prompt_choices(
                "Couldn't ascertain one of [%s] from file name. Convert to"
                % ", ".join(valid_workspace_formats),
                choices=t.cast(t.List[str], valid_workspace_formats),
                default="yaml",
            )
            assert is_valid_ext(_workspace_format)
            workspace_format = _workspace_format

    if workspace_format == "yaml":
        workspace = configparser.dump(
            fmt="yaml",
            indent=2,
            default_flow_style=False,
            safe=True,
        )
    elif workspace_format == "json":
        workspace = configparser.dump(fmt="json", indent=2)

    if args.answer_yes or prompt_yes_no("Save to %s?" % dest):
        destdir = os.path.dirname(dest)
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        with open(dest, "w", encoding=locale.getpreferredencoding(False)) as buf:
            buf.write(workspace)

        if not args.quiet:
            print("Saved to %s." % dest)
