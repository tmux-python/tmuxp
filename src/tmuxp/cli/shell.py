import argparse
import os
import typing as t

from libtmux.server import Server

from .. import util
from .._compat import PY3, PYMINOR

if t.TYPE_CHECKING:
    from typing_extensions import Literal, TypeAlias

    CLIColorsLiteral: TypeAlias = Literal[56, 88]
    CLIShellLiteral: TypeAlias = Literal[
        "best", "pdb", "code", "ptipython", "ptpython", "ipython", "bpython"
    ]


class CLIShellNamespace(argparse.Namespace):
    session_name: str
    socket_name: t.Optional[str]
    socket_path: t.Optional[str]
    colors: t.Optional["CLIColorsLiteral"]
    log_file: t.Optional[str]
    window_name: t.Optional[str]
    command: t.Optional[str]
    shell: t.Optional["CLIShellLiteral"]
    use_pythonrc: bool
    use_vi_mode: bool


def create_shell_subparser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("session_name", metavar="session-name", nargs="?")
    parser.add_argument("window_name", metavar="window-name", nargs="?")
    parser.add_argument(
        "-S", dest="socket_path", metavar="socket-path", help="pass-through for tmux -S"
    )
    parser.add_argument(
        "-L", dest="socket_name", metavar="socket-name", help="pass-through for tmux -L"
    )
    parser.add_argument(
        "-c",
        dest="command",
        help="instead of opening shell, execute python code in libtmux and exit",
    )

    shells = parser.add_mutually_exclusive_group()
    shells.add_argument(
        "--best",
        dest="shell",
        const="best",
        action="store_const",
        help="use best shell available in site packages",
        default="best",
    )
    shells.add_argument(
        "--pdb",
        dest="shell",
        const="pdb",
        action="store_const",
        help="use plain pdb",
    )
    shells.add_argument(
        "--code",
        dest="shell",
        const="code",
        action="store_const",
        help="use stdlib's code.interact()",
    )
    shells.add_argument(
        "--ptipython",
        dest="shell",
        const="ptipython",
        action="store_const",
        help="use ptpython + ipython",
    )
    shells.add_argument(
        "--ptpython",
        dest="shell",
        const="ptpython",
        action="store_const",
        help="use ptpython",
    )
    shells.add_argument(
        "--ipython",
        dest="shell",
        const="ipython",
        action="store_const",
        help="use ipython",
    )
    shells.add_argument(
        "--bpython",
        dest="shell",
        const="bpython",
        action="store_const",
        help="use bpython",
    )

    parser.add_argument(
        "--use-pythonrc",
        dest="use_pythonrc",
        action="store_true",
        help="load PYTHONSTARTUP env var and ~/.pythonrc.py script in --code",
        default=False,
    )
    parser.add_argument(
        "--no-startup",
        dest="use_pythonrc",
        action="store_false",
        help="load PYTHONSTARTUP env var and ~/.pythonrc.py script in --code",
        default=False,
    )
    parser.add_argument(
        "--use-vi-mode",
        dest="use_vi_mode",
        action="store_true",
        help="use vi-mode in ptpython/ptipython",
        default=False,
    )
    parser.add_argument(
        "--no-vi-mode",
        dest="use_vi_mode",
        action="store_false",
        help="use vi-mode in ptpython/ptipython",
        default=False,
    )
    return parser


def command_shell(
    args: CLIShellNamespace,
    parser: t.Optional[argparse.ArgumentParser] = None,
) -> None:
    """Launch python shell for tmux server, session, window and pane.

    Priority given to loaded session/window/pane objects:

    - session_name and window_name arguments
    - current shell: envvar ``TMUX_PANE`` for determining window and session
    - :attr:`libtmux.Server.attached_sessions`, :attr:`libtmux.Session.attached_window`,
      :attr:`libtmux.Window.attached_pane`
    """
    server = Server(socket_name=args.socket_name, socket_path=args.socket_path)

    util.raise_if_tmux_not_running(server=server)

    current_pane = util.get_current_pane(server=server)

    session = util.get_session(
        server=server, session_name=args.session_name, current_pane=current_pane
    )

    window = util.get_window(
        session=session, window_name=args.window_name, current_pane=current_pane
    )

    pane = util.get_pane(window=window, current_pane=current_pane)  # NOQA: F841

    if args.command is not None:
        exec(args.command)
    else:
        if args.shell == "pdb" or (
            os.getenv("PYTHONBREAKPOINT") and PY3 and PYMINOR >= 7
        ):
            from tmuxp._compat import breakpoint as tmuxp_breakpoint

            tmuxp_breakpoint()
            return
        else:
            from ..shell import launch

            launch(
                shell=args.shell,
                use_pythonrc=args.use_pythonrc,  # shell: code
                use_vi_mode=args.use_vi_mode,  # shell: ptpython, ptipython
                # tmux environment / libtmux variables
                server=server,
                session=session,
                window=window,
                pane=pane,
            )
