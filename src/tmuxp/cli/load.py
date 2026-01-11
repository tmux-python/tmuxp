"""CLI for ``tmuxp load`` subcommand."""

from __future__ import annotations

import argparse
import importlib
import logging
import os
import pathlib
import shutil
import sys
import typing as t

from libtmux.server import Server

from tmuxp import exc, log, util
from tmuxp._internal import config_reader
from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace import loader
from tmuxp.workspace.builder import WorkspaceBuilder
from tmuxp.workspace.finders import find_workspace_file, get_workspace_dir

from ._colors import ColorMode, Colors, build_description, get_color_mode
from .utils import prompt_choices, prompt_yes_no, tmuxp_echo

LOAD_DESCRIPTION = build_description(
    """
    Load tmuxp workspace file(s) and create or attach to a tmux session.
    """,
    (
        (
            None,
            [
                "tmuxp load myproject",
                "tmuxp load ./workspace.yaml",
                "tmuxp load -d myproject",
                "tmuxp load -y dev staging",
                "tmuxp load -L other-socket myproject",
                "tmuxp load -a myproject",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    from typing import TypeAlias

    from libtmux.session import Session
    from typing_extensions import NotRequired, TypedDict

    from tmuxp.types import StrPath

    CLIColorsLiteral: TypeAlias = t.Literal[56, 88]
    CLIColorModeLiteral: TypeAlias = t.Literal["auto", "always", "never"]

    class OptionOverrides(TypedDict):
        """Optional argument overrides for tmuxp load."""

        detached: NotRequired[bool]
        new_session_name: NotRequired[str | None]


class CLILoadNamespace(argparse.Namespace):
    """Typed :class:`argparse.Namespace` for tmuxp load command."""

    workspace_files: list[str]
    socket_name: str | None
    socket_path: str | None
    tmux_config_file: str | None
    new_session_name: str | None
    answer_yes: bool | None
    detached: bool
    append: bool | None
    colors: CLIColorsLiteral | None
    color: CLIColorModeLiteral
    log_file: str | None


def load_plugins(
    session_config: dict[str, t.Any],
    colors: Colors | None = None,
) -> list[t.Any]:
    """Load and return plugins in workspace.

    Parameters
    ----------
    session_config : dict
        Session configuration dictionary.
    colors : Colors | None
        Colors instance for output formatting. If None, uses AUTO mode.

    Returns
    -------
    list
        List of loaded plugin instances.

    Examples
    --------
    Empty config returns empty list:

    >>> from tmuxp.cli.load import load_plugins
    >>> load_plugins({'session_name': 'test'})
    []

    With explicit Colors instance:

    >>> from tmuxp.cli._colors import ColorMode, Colors
    >>> colors = Colors(ColorMode.NEVER)
    >>> load_plugins({'session_name': 'test'}, colors=colors)
    []
    """
    if colors is None:
        colors = Colors(ColorMode.AUTO)

    plugins = []
    if "plugins" in session_config:
        for plugin in session_config["plugins"]:
            try:
                module_name = plugin.split(".")
                module_name = ".".join(module_name[:-1])
                plugin_name = plugin.split(".")[-1]
            except AttributeError as error:
                tmuxp_echo(
                    colors.error("[Plugin Error]")
                    + f" Couldn't load {plugin}\n"
                    + colors.warning(f"{error}"),
                )
                sys.exit(1)

            try:
                plugin = getattr(importlib.import_module(module_name), plugin_name)
                plugins.append(plugin())
            except exc.TmuxpPluginException as error:
                if not prompt_yes_no(
                    f"{colors.warning(str(error))}Skip loading {plugin_name}?",
                    default=True,
                    color_mode=colors.mode,
                ):
                    tmuxp_echo(
                        colors.warning("[Not Skipping]")
                        + " Plugin versions constraint not met. Exiting...",
                    )
                    sys.exit(1)
            except (ImportError, AttributeError) as error:
                tmuxp_echo(
                    colors.error("[Plugin Error]")
                    + f" Couldn't load {plugin}\n"
                    + colors.warning(f"{error}"),
                )
                sys.exit(1)

    return plugins


def _reattach(builder: WorkspaceBuilder, colors: Colors | None = None) -> None:
    """
    Reattach session (depending on env being inside tmux already or not).

    Parameters
    ----------
    builder: :class:`workspace.builder.WorkspaceBuilder`
    colors : Colors | None
        Optional Colors instance for styled output.

    Notes
    -----
    If ``TMUX`` environmental variable exists in the environment this script is
    running, that means we're in a tmux client. So ``tmux switch-client`` will
    load the session.

    If not, ``tmux attach-session`` loads the client to the target session.
    """
    assert builder.session is not None
    for plugin in builder.plugins:
        plugin.reattach(builder.session)
        proc = builder.session.cmd("display-message", "-p", "'#S'")
        for line in proc.stdout:
            print(colors.info(line) if colors else line)  # NOQA: T201 RUF100

    if "TMUX" in os.environ:
        builder.session.switch_client()

    else:
        builder.session.attach()


def _load_attached(builder: WorkspaceBuilder, detached: bool) -> None:
    """
    Load workspace in new session.

    Parameters
    ----------
    builder: :class:`workspace.builder.WorkspaceBuilder`
    detached : bool
    """
    builder.build()
    assert builder.session is not None

    if "TMUX" in os.environ:  # tmuxp ran from inside tmux
        # unset TMUX, save it, e.g. '/tmp/tmux-1000/default,30668,0'
        tmux_env = os.environ.pop("TMUX")

        builder.session.switch_client()  # switch client to new session

        os.environ["TMUX"] = tmux_env  # set TMUX back again
    elif not detached:
        builder.session.attach()


def _load_detached(builder: WorkspaceBuilder, colors: Colors | None = None) -> None:
    """
    Load workspace in new session but don't attach.

    Parameters
    ----------
    builder: :class:`workspace.builder.WorkspaceBuilder`
    colors : Colors | None
        Optional Colors instance for styled output.
    """
    builder.build()

    assert builder.session is not None

    msg = "Session created in detached state."
    print(colors.info(msg) if colors else msg)  # NOQA: T201 RUF100


def _load_append_windows_to_current_session(builder: WorkspaceBuilder) -> None:
    """
    Load workspace as new windows in current session.

    Parameters
    ----------
    builder: :class:`workspace.builder.WorkspaceBuilder`
    """
    current_attached_session = builder.find_current_attached_session()
    builder.build(current_attached_session, append=True)
    assert builder.session is not None


def _setup_plugins(builder: WorkspaceBuilder) -> Session:
    """Execute hooks for plugins running after ``before_script``.

    Parameters
    ----------
    builder: :class:`workspace.builder.WorkspaceBuilder`
    """
    assert builder.session is not None
    for plugin in builder.plugins:
        plugin.before_script(builder.session)

    return builder.session


def load_workspace(
    workspace_file: StrPath,
    socket_name: str | None = None,
    socket_path: str | None = None,
    tmux_config_file: str | None = None,
    new_session_name: str | None = None,
    colors: int | None = None,
    detached: bool = False,
    answer_yes: bool = False,
    append: bool = False,
    cli_colors: Colors | None = None,
) -> Session | None:
    """Entrypoint for ``tmuxp load``, load a tmuxp "workspace" session via config file.

    Parameters
    ----------
    workspace_file : list of str
        paths or session names to workspace files
    socket_name : str, optional
        ``tmux -L <socket-name>``
    socket_path: str, optional
        ``tmux -S <socket-path>``
    new_session_name: str, options
        ``tmux new -s <new_session_name>``
    colors : int, optional
        Force tmux to support 256 or 88 colors.
    detached : bool
        Force detached state. default False.
    answer_yes : bool
        Assume yes when given prompt to attach in new session.
        Default False.
    append : bool
       Assume current when given prompt to append windows in same session.
       Default False.
    cli_colors : Colors, optional
        Colors instance for CLI output formatting. If None, uses AUTO mode.

    Notes
    -----
    tmuxp will check and load a workspace file. The file will use ConfigReader
    to load a JSON/YAML into a :py:obj:`dict`. Then :func:`loader.expand` and
    :func:`loader.trickle` will be used to expand any shorthands, template
    variables, or file paths relative to where the config/script is executed
    from.

    :func:`loader.expand` accepts the directory of the config file, so the
    user's workspace can resolve absolute paths relative to where the
    workspace file is. In otherwords, if a workspace file at */var/moo/hi.yaml*
    has *./* in its workspaces, we want to be sure any file path with *./* is
    relative to */var/moo*, not the user's PWD.

    A :class:`libtmux.Server` object is created. No tmux server is started yet,
    just the object.

    The prepared workspace and its server object is passed into an instance
    of :class:`~tmuxp.workspace.builder.WorkspaceBuilder`.

    A sanity check against :meth:`libtmux.common.which` is ran. It will raise
    an exception if tmux isn't found.

    If a tmux session under the same name as ``session_name`` in the tmuxp
    workspace exists, tmuxp offers to attach the session. Currently, tmuxp
    does not allow appending a workspace / incremental building on top of a
    current session (pull requests are welcome!).

    :meth:`~tmuxp.workspace.builder.build` will build the session in
    the background via using tmux's detached state (``-d``).

    After the session (workspace) is built, unless the user decided to load
    the session in the background via ``tmuxp -d`` (which is in the spirit
    of tmux's ``-d``), we need to prompt the user to attach the session.

    If the user is already inside a tmux client, which we detect via the
    ``TMUX`` environment variable bring present, we will prompt the user to
    switch their current client to it.

    If they're outside of tmux client - in a plain-old PTY - we will
    automatically ``attach``.

    If an exception is raised during the building of the workspace, tmuxp will
    prompt to cleanup (``$ tmux kill-session``) the session on the user's
    behalf. An exception raised during this process means it's not easy to
    predict how broken the session is.
    """
    # Initialize CLI colors if not provided
    if cli_colors is None:
        cli_colors = Colors(ColorMode.AUTO)

    # get the canonical path, eliminating any symlinks
    if isinstance(workspace_file, (str, os.PathLike)):
        workspace_file = pathlib.Path(workspace_file)

    tmuxp_echo(
        cli_colors.info("[Loading]")
        + " "
        + cli_colors.highlight(str(PrivatePath(workspace_file))),
    )

    # ConfigReader allows us to open a yaml or json file as a dict
    raw_workspace = config_reader.ConfigReader._from_file(workspace_file) or {}

    # shapes workspaces relative to config / profile file location
    expanded_workspace = loader.expand(
        raw_workspace,
        cwd=os.path.dirname(workspace_file),
    )

    # Overridden session name
    if new_session_name:
        expanded_workspace["session_name"] = new_session_name

    # propagate workspace inheritance (e.g. session -> window, window -> pane)
    expanded_workspace = loader.trickle(expanded_workspace)

    t = Server(  # create tmux server object
        socket_name=socket_name,
        socket_path=socket_path,
        config_file=tmux_config_file,
        colors=colors,
    )

    shutil.which("tmux")  # raise exception if tmux not found

    try:  # load WorkspaceBuilder object for tmuxp workspace / tmux server
        builder = WorkspaceBuilder(
            session_config=expanded_workspace,
            plugins=load_plugins(expanded_workspace, colors=cli_colors),
            server=t,
        )
    except exc.EmptyWorkspaceException:
        tmuxp_echo(
            cli_colors.warning("[Warning]")
            + f" {PrivatePath(workspace_file)} is empty or parsed no workspace data",
        )
        return None

    session_name = expanded_workspace["session_name"]

    # if the session already exists, prompt the user to attach
    if builder.session_exists(session_name) and not append:
        if not detached and (
            answer_yes
            or prompt_yes_no(
                f"{cli_colors.highlight(session_name)} is already running. Attach?",
                default=True,
                color_mode=cli_colors.mode,
            )
        ):
            _reattach(builder, cli_colors)
        return None

    try:
        if detached:
            _load_detached(builder, cli_colors)
            return _setup_plugins(builder)

        if append:
            if "TMUX" in os.environ:  # tmuxp ran from inside tmux
                _load_append_windows_to_current_session(builder)
            else:
                _load_attached(builder, detached)

            return _setup_plugins(builder)

        # append and answer_yes have no meaning if specified together
        if answer_yes:
            _load_attached(builder, detached)
            return _setup_plugins(builder)

        if "TMUX" in os.environ:  # tmuxp ran from inside tmux
            msg = (
                "Already inside TMUX, switch to session? yes/no\n"
                "Or (a)ppend windows in the current active session?\n[y/n/a]"
            )
            options = ["y", "n", "a"]
            choice = prompt_choices(msg, choices=options, color_mode=cli_colors.mode)

            if choice == "y":
                _load_attached(builder, detached)
            elif choice == "a":
                _load_append_windows_to_current_session(builder)
            else:
                _load_detached(builder, cli_colors)
        else:
            _load_attached(builder, detached)

    except exc.TmuxpException as e:
        import traceback

        tmuxp_echo(traceback.format_exc())
        tmuxp_echo(cli_colors.error("[Error]") + f" {e}")

        choice = prompt_choices(
            cli_colors.error("Error loading workspace.")
            + " (k)ill, (a)ttach, (d)etach?",
            choices=["k", "a", "d"],
            default="k",
            color_mode=cli_colors.mode,
        )

        if choice == "k":
            if builder.session is not None:
                builder.session.kill()
                tmuxp_echo(cli_colors.muted("Session killed."))
        elif choice == "a":
            _reattach(builder, cli_colors)
        else:
            sys.exit()

    return _setup_plugins(builder)


def create_load_subparser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``load`` subcommand."""
    workspace_files = parser.add_argument(
        "workspace_files",
        nargs="+",
        metavar="workspace-file",
        help="filepath to session or filename of session in tmuxp workspace directory",
    )
    parser.add_argument(
        "-L",
        dest="socket_name",
        metavar="socket_name",
        action="store",
        help="passthru to tmux(1) -L",
    )
    parser.add_argument(
        "-S",
        dest="socket_path",
        metavar="socket_path",
        action="store",
        help="passthru to tmux(1) -S",
    )

    tmux_config_file = parser.add_argument(
        "-f",
        dest="tmux_config_file",
        metavar="tmux_config_file",
        help="passthru to tmux(1) -f",
    )

    parser.add_argument(
        "-s",
        dest="new_session_name",
        metavar="new_session_name",
        help="start new session with new session name",
    )
    parser.add_argument(
        "--yes",
        "-y",
        dest="answer_yes",
        action="store_true",
        help="always answer yes",
    )
    parser.add_argument(
        "-d",
        dest="detached",
        action="store_true",
        help="load the session without attaching it",
    )
    parser.add_argument(
        "-a",
        "--append",
        dest="append",
        action="store_true",
        help="load workspace, appending windows to the current session",
    )
    colorsgroup = parser.add_mutually_exclusive_group()

    colorsgroup.add_argument(
        "-2",
        dest="colors",
        action="store_const",
        const=256,
        help="force tmux to assume the terminal supports 256 colours.",
    )

    colorsgroup.add_argument(
        "-8",
        dest="colors",
        action="store_const",
        const=88,
        help="like -2, but indicates that the terminal supports 88 colours.",
    )
    parser.set_defaults(colors=None)

    log_file = parser.add_argument(
        "--log-file",
        metavar="file_path",
        action="store",
        help="file to log errors/output to",
    )

    try:
        import shtab

        workspace_files.complete = shtab.FILE  # type: ignore
        tmux_config_file.complete = shtab.FILE  # type: ignore
        log_file.complete = shtab.FILE  # type: ignore
    except ImportError:
        pass

    return parser


def command_load(
    args: CLILoadNamespace,
    parser: argparse.ArgumentParser | None = None,
) -> None:
    """Load a tmux workspace from each WORKSPACE_FILE.

    WORKSPACE_FILE is a specifier for a workspace file.

    If WORKSPACE_FILE is a path to a directory, tmuxp will search it for
    ".tmuxp.{yaml,yml,json}".

    If WORKSPACE_FILE is has no directory component and only a filename, e.g.
    "myworkspace.yaml", tmuxp will search the users's workspace directory for that
    file.

    If WORKSPACE_FILE has no directory component, and only a name with no extension,
    e.g. "myworkspace", tmuxp will search the users's workspace directory for any
    file with the extension ".yaml", ".yml", or ".json" that matches that name.

    If multiple workspace files that match a given WORKSPACE_FILE are found, tmuxp
    will warn and pick the first one found.

    If multiple WORKSPACE_FILEs are provided, workspaces will be created for all of
    them. The last one provided will be attached. The others will be created in
    detached mode.
    """
    util.oh_my_zsh_auto_title()

    # Create Colors instance based on CLI --color flag
    cli_colors = Colors(get_color_mode(args.color))

    if args.log_file:
        logfile_handler = logging.FileHandler(args.log_file)
        logfile_handler.setFormatter(log.LogFormatter())
        # Add handler to tmuxp root logger to capture all tmuxp log messages
        tmuxp_logger = logging.getLogger("tmuxp")
        tmuxp_logger.setLevel(logging.INFO)  # Ensure logger level allows INFO
        tmuxp_logger.addHandler(logfile_handler)

    if args.workspace_files is None or len(args.workspace_files) == 0:
        tmuxp_echo(cli_colors.error("Enter at least one config"))
        if parser is not None:
            parser.print_help()
        sys.exit()
        return

    last_idx = len(args.workspace_files) - 1
    original_detached_option = args.detached
    original_new_session_name = args.new_session_name

    for idx, workspace_file in enumerate(args.workspace_files):
        workspace_file = find_workspace_file(
            workspace_file,
            workspace_dir=get_workspace_dir(),
        )

        detached = original_detached_option
        new_session_name = original_new_session_name

        if last_idx > 0 and idx < last_idx:
            detached = True
            new_session_name = None

        load_workspace(
            workspace_file,
            socket_name=args.socket_name,
            socket_path=args.socket_path,
            tmux_config_file=args.tmux_config_file,
            new_session_name=new_session_name,
            colors=args.colors,
            detached=detached,
            answer_yes=args.answer_yes or False,
            append=args.append or False,
            cli_colors=cli_colors,
        )
