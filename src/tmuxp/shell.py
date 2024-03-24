"""Utility and helper methods for tmuxp."""

import logging
import os
import pathlib
import typing as t

logger = logging.getLogger(__name__)

if t.TYPE_CHECKING:
    from types import ModuleType

    from libtmux.pane import Pane
    from libtmux.server import Server
    from libtmux.session import Session
    from libtmux.window import Window
    from typing_extensions import NotRequired, TypeAlias, TypedDict, Unpack

    CLIShellLiteral: TypeAlias = t.Literal[
        "best",
        "pdb",
        "code",
        "ptipython",
        "ptpython",
        "ipython",
        "bpython",
    ]

    class LaunchOptionalImports(TypedDict):
        """tmuxp shell optional imports."""

        server: NotRequired["Server"]
        session: NotRequired["Session"]
        window: NotRequired["Window"]
        pane: NotRequired["Pane"]

    class LaunchImports(t.TypedDict):
        """tmuxp shell launch import mapping."""

        libtmux: ModuleType
        Server: t.Type[Server]
        Session: t.Type[Session]
        Window: t.Type[Window]
        Pane: t.Type[Pane]
        server: t.Optional["Server"]
        session: t.Optional["Session"]
        window: t.Optional["Window"]
        pane: t.Optional["Pane"]


def has_ipython() -> bool:
    """Return True if ipython is installed."""
    try:
        from IPython import start_ipython  # NOQA F841
    except ImportError:
        try:
            from IPython.Shell import IPShell  # NOQA F841
        except ImportError:
            return False

    return True


def has_ptpython() -> bool:
    """Return True if ptpython is installed."""
    try:
        from ptpython.repl import embed, run_config  # F841
    except ImportError:
        try:
            from prompt_toolkit.contrib.repl import embed, run_config  # NOQA F841
        except ImportError:
            return False

    return True


def has_ptipython() -> bool:
    """Return True if ptpython + ipython are both installed."""
    try:
        from ptpython.ipython import embed  # F841
        from ptpython.repl import run_config  # F841
    except ImportError:
        try:
            from prompt_toolkit.contrib.ipython import embed  # NOQA F841
            from prompt_toolkit.contrib.repl import run_config  # NOQA F841
        except ImportError:
            return False

    return True


def has_bpython() -> bool:
    """Return True if bpython is installed."""
    try:
        from bpython import embed  # NOQA F841
    except ImportError:
        return False
    return True


def detect_best_shell() -> "CLIShellLiteral":
    """Return the best, most feature-rich shell available."""
    if has_ptipython():
        return "ptipython"
    if has_ptpython():
        return "ptpython"
    if has_ipython():
        return "ipython"
    if has_bpython():
        return "bpython"
    return "code"


def get_bpython(
    options: "LaunchOptionalImports",
    extra_args: t.Optional[t.Dict[str, t.Any]] = None,
) -> t.Callable[[], None]:
    """Return bpython shell."""
    if extra_args is None:
        extra_args = {}

    from bpython import embed  # F841

    def launch_bpython() -> None:
        imported_objects = get_launch_args(**options)
        kwargs = {}
        if extra_args:
            kwargs["args"] = extra_args
        embed(imported_objects, **kwargs)

    return launch_bpython


def get_ipython_arguments() -> t.List[str]:
    """Return ipython shell args via ``IPYTHON_ARGUMENTS`` environment variables."""
    ipython_args = "IPYTHON_ARGUMENTS"
    return os.environ.get(ipython_args, "").split()


def get_ipython(
    options: "LaunchOptionalImports",
    **extra_args: t.Dict[str, t.Any],
) -> t.Any:
    """Return ipython shell."""
    try:
        from IPython import start_ipython

        def launch_ipython() -> None:
            imported_objects = get_launch_args(**options)
            ipython_arguments = extra_args or get_ipython_arguments()
            start_ipython(argv=ipython_arguments, user_ns=imported_objects)

        return launch_ipython  # NOQA: TRY300
    except ImportError:
        # IPython < 0.11
        # Explicitly pass an empty list as arguments, because otherwise
        # IPython would use sys.argv from this script.
        # Notebook not supported for IPython < 0.11.
        from IPython.Shell import IPShell

        def launch_ipython() -> None:
            imported_objects = get_launch_args(**options)
            shell = IPShell(argv=[], user_ns=imported_objects)
            shell.mainloop()

        return launch_ipython


def get_ptpython(options: "LaunchOptionalImports", vi_mode: bool = False) -> t.Any:
    """Return ptpython shell."""
    try:
        from ptpython.repl import embed, run_config
    except ImportError:
        from prompt_toolkit.contrib.repl import embed, run_config

    def launch_ptpython() -> None:
        imported_objects = get_launch_args(**options)
        history_filename = str(pathlib.Path("~/.ptpython_history").expanduser())
        embed(
            globals=imported_objects,
            history_filename=history_filename,
            vi_mode=vi_mode,
            configure=run_config,
        )

    return launch_ptpython


def get_ptipython(options: "LaunchOptionalImports", vi_mode: bool = False) -> t.Any:
    """Based on django-extensions.

    Run renamed to launch, get_imported_objects renamed to get_launch_args
    """
    try:
        from ptpython.ipython import embed
        from ptpython.repl import run_config
    except ImportError:
        # prompt_toolkit < v0.27
        from prompt_toolkit.contrib.ipython import embed
        from prompt_toolkit.contrib.repl import run_config

    def launch_ptipython() -> None:
        imported_objects = get_launch_args(**options)
        history_filename = str(pathlib.Path("~/.ptpython_history").expanduser())
        embed(
            user_ns=imported_objects,
            history_filename=history_filename,
            vi_mode=vi_mode,
            configure=run_config,
        )

    return launch_ptipython


def get_launch_args(**kwargs: "Unpack[LaunchOptionalImports]") -> "LaunchImports":
    """Return tmuxp shell launch arguments, counting for overrides."""
    import libtmux
    from libtmux.pane import Pane
    from libtmux.server import Server
    from libtmux.session import Session
    from libtmux.window import Window

    return {
        "libtmux": libtmux,
        "Server": Server,
        "Session": Session,
        "Window": Window,
        "Pane": Pane,
        "server": kwargs.get("server"),
        "session": kwargs.get("session"),
        "window": kwargs.get("window"),
        "pane": kwargs.get("pane"),
    }


def get_code(use_pythonrc: bool, imported_objects: "LaunchImports") -> t.Any:
    """Launch basic python shell via :mod:`code`."""
    import code

    try:
        # Try activating rlcompleter, because it's handy.
        import readline
    except ImportError:
        pass
    else:
        # We don't have to wrap the following import in a 'try', because
        # we already know 'readline' was imported successfully.
        import rlcompleter

        readline.set_completer(
            rlcompleter.Completer(
                imported_objects,  # type:ignore
            ).complete,
        )
        # Enable tab completion on systems using libedit (e.g. macOS).
        # These lines are copied from Lib/site.py on Python 3.4.
        readline_doc = getattr(readline, "__doc__", "")
        if readline_doc is not None and "libedit" in readline_doc:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab:complete")

    # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
    # conventions and get $PYTHONSTARTUP first then .pythonrc.py.
    if use_pythonrc:
        PYTHONSTARTUP = os.environ.get("PYTHONSTARTUP")
        for pythonrc in {
            *([pathlib.Path(PYTHONSTARTUP)] if PYTHONSTARTUP is not None else []),
            pathlib.Path("~/.pythonrc.py").expanduser(),
        }:
            if not pythonrc:
                continue
            if not pythonrc.is_file():
                continue
            with pythonrc.open() as handle:
                pythonrc_code = handle.read()
            # Match the behavior of the cpython shell where an error in
            # PYTHONSTARTUP prints an exception and continues.
            exec(
                compile(pythonrc_code, pythonrc, "exec"),
                imported_objects,  # type:ignore
            )

    def launch_code() -> None:
        code.interact(local=imported_objects)

    return launch_code


def launch(
    shell: t.Optional["CLIShellLiteral"] = "best",
    use_pythonrc: bool = False,
    use_vi_mode: bool = False,
    **kwargs: "Unpack[LaunchOptionalImports]",
) -> None:
    """Launch interactive libtmux shell for tmuxp shell."""
    # Also allowing passing shell='code' to force using code.interact
    imported_objects = get_launch_args(**kwargs)

    if shell == "best":
        shell = detect_best_shell()

    if shell == "ptipython":
        launch = get_ptipython(options=kwargs, vi_mode=use_vi_mode)
    elif shell == "ptpython":
        launch = get_ptpython(options=kwargs, vi_mode=use_vi_mode)
    elif shell == "ipython":
        launch = get_ipython(options=kwargs)
    elif shell == "bpython":
        launch = get_bpython(options=kwargs)
    else:
        launch = get_code(use_pythonrc=use_pythonrc, imported_objects=imported_objects)

    launch()
