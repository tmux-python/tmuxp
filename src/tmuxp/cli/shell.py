import os

import click

from libtmux import Server

from .. import util
from .._compat import PY3, PYMINOR


@click.command(name="shell")
@click.argument("session_name", nargs=1, required=False)
@click.argument("window_name", nargs=1, required=False)
@click.option("-S", "socket_path", help="pass-through for tmux -S")
@click.option("-L", "socket_name", help="pass-through for tmux -L")
@click.option(
    "-c",
    "command",
    help="Instead of opening shell, execute python code in libtmux and exit",
)
@click.option(
    "--best",
    "shell",
    flag_value="best",
    help="Use best shell available in site packages",
    default=True,
)
@click.option("--pdb", "shell", flag_value="pdb", help="Use plain pdb")
@click.option("--code", "shell", flag_value="code", help="Use stdlib's code.interact()")
@click.option(
    "--ptipython", "shell", flag_value="ptipython", help="Use ptpython + ipython"
)
@click.option("--ptpython", "shell", flag_value="ptpython", help="Use ptpython")
@click.option("--ipython", "shell", flag_value="ipython", help="Use ipython")
@click.option("--bpython", "shell", flag_value="bpython", help="Use bpython")
@click.option(
    "--use-pythonrc/--no-startup",
    "use_pythonrc",
    help="Load PYTHONSTARTUP env var and ~/.pythonrc.py script in --code",
    default=False,
)
@click.option(
    "--use-vi-mode/--no-vi-mode",
    "use_vi_mode",
    help="Use vi-mode in ptpython/ptipython",
    default=False,
)
def command_shell(
    session_name,
    window_name,
    socket_name,
    socket_path,
    command,
    shell,
    use_pythonrc,
    use_vi_mode,
):
    """Launch python shell for tmux server, session, window and pane.

    Priority given to loaded session/window/pane objects:

    - session_name and window_name arguments
    - current shell: envvar ``TMUX_PANE`` for determining window and session
    - :attr:`libtmux.Server.attached_sessions`, :attr:`libtmux.Session.attached_window`,
      :attr:`libtmux.Window.attached_pane`
    """
    server = Server(socket_name=socket_name, socket_path=socket_path)

    util.raise_if_tmux_not_running(server=server)

    current_pane = util.get_current_pane(server=server)

    session = util.get_session(
        server=server, session_name=session_name, current_pane=current_pane
    )

    window = util.get_window(
        session=session, window_name=window_name, current_pane=current_pane
    )

    pane = util.get_pane(window=window, current_pane=current_pane)  # NOQA: F841

    if command is not None:
        exec(command)
    else:
        if shell == "pdb" or (os.getenv("PYTHONBREAKPOINT") and PY3 and PYMINOR >= 7):
            from tmuxp._compat import breakpoint as tmuxp_breakpoint

            tmuxp_breakpoint()
            return
        else:
            from ..shell import launch

            launch(
                shell=shell,
                use_pythonrc=use_pythonrc,  # shell: code
                use_vi_mode=use_vi_mode,  # shell: ptpython, ptipython
                # tmux environment / libtmux variables
                server=server,
                session=session,
                window=window,
                pane=pane,
            )
