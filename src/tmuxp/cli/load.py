"""CLI for ``tmuxp load`` subcommand."""

from __future__ import annotations

import argparse
import contextlib
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
from ._progress import (
    DEFAULT_OUTPUT_LINES,
    SUCCESS_TEMPLATE,
    Spinner,
    _SafeFormatMap,
    resolve_progress_format,
)
from .utils import prompt_choices, prompt_yes_no, tmuxp_echo

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _silence_stream_handlers(logger_name: str = "tmuxp") -> t.Iterator[None]:
    """Temporarily raise StreamHandler level to WARNING while spinner is active.

    INFO/DEBUG log records are diagnostics for aggregators, not user-facing output;
    the spinner is the user-facing progress channel. Restores original levels on exit.
    """
    _log = logging.getLogger(logger_name)
    saved: list[tuple[logging.StreamHandler[t.Any], int]] = [
        (h, h.level)
        for h in _log.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
    ]
    for h, _ in saved:
        h.setLevel(logging.WARNING)
    try:
        yield
    finally:
        for h, level in saved:
            h.setLevel(level)


class _TmuxCommandDebugHandler(logging.Handler):
    """Logging handler that prints tmux commands from libtmux's structured logs."""

    def __init__(self, colors: Colors) -> None:
        super().__init__()
        self._colors = colors

    def emit(self, record: logging.LogRecord) -> None:
        """Print tmux command if present in the log record's extra fields."""
        cmd = getattr(record, "tmux_cmd", None)
        if cmd is not None:
            tmuxp_echo(self._colors.muted("$ ") + self._colors.info(str(cmd)))


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
    here: bool | None
    colors: CLIColorsLiteral | None
    color: CLIColorModeLiteral
    log_file: str | None
    log_level: str
    progress_format: str | None
    panel_lines: int | None
    no_progress: bool
    no_shell_command_before: bool
    debug: bool
    set: list[str]


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
                logger.debug("plugin load failed", exc_info=True)
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
                    logger.warning(
                        "plugin version constraint not met, user declined skip",
                    )
                    tmuxp_echo(
                        colors.warning("[Not Skipping]")
                        + " Plugin versions constraint not met. Exiting...",
                    )
                    sys.exit(1)
            except (ImportError, AttributeError) as error:
                logger.debug("plugin import failed", exc_info=True)
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
            tmuxp_echo(colors.info(line) if colors else line)
            logger.debug(
                "reattach display-message output",
                extra={"tmux_stdout": [line.strip()]},
            )

    if "TMUX" in os.environ:
        builder.session.switch_client()

    else:
        builder.session.attach()


def _load_attached(
    builder: WorkspaceBuilder,
    detached: bool,
    pre_attach_hook: t.Callable[[], None] | None = None,
) -> None:
    """
    Load workspace in new session.

    Parameters
    ----------
    builder: :class:`workspace.builder.WorkspaceBuilder`
    detached : bool
    pre_attach_hook : callable, optional
        called after build, before attach/switch_client; use to stop the spinner
        so its cleanup sequences don't appear inside the tmux pane.
    """
    builder.build()
    assert builder.session is not None

    if pre_attach_hook is not None:
        pre_attach_hook()

    if "TMUX" in os.environ:  # tmuxp ran from inside tmux
        # unset TMUX, save it, e.g. '/tmp/tmux-1000/default,30668,0'
        tmux_env = os.environ.pop("TMUX")

        builder.session.switch_client()  # switch client to new session

        os.environ["TMUX"] = tmux_env  # set TMUX back again
    elif not detached:
        builder.session.attach()


def _load_detached(
    builder: WorkspaceBuilder,
    colors: Colors | None = None,
    pre_output_hook: t.Callable[[], None] | None = None,
) -> None:
    """
    Load workspace in new session but don't attach.

    Parameters
    ----------
    builder: :class:`workspace.builder.WorkspaceBuilder`
    colors : Colors | None
        Optional Colors instance for styled output.
    pre_output_hook : Callable | None
        Called after build but before printing, e.g. to stop a spinner.
    """
    builder.build()

    assert builder.session is not None

    if pre_output_hook is not None:
        pre_output_hook()

    msg = "Session created in detached state."
    tmuxp_echo(colors.info(msg) if colors else msg)
    logger.info("session created in detached state")


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


def _load_here_in_current_session(builder: WorkspaceBuilder) -> None:
    """Load workspace reusing current window for first window.

    Parameters
    ----------
    builder: :class:`workspace.builder.WorkspaceBuilder`

    Examples
    --------
    >>> from tmuxp.cli.load import _load_here_in_current_session
    >>> callable(_load_here_in_current_session)
    True
    """
    current_attached_session = builder.find_current_attached_session()
    builder.build(current_attached_session, here=True)
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


def _dispatch_build(
    builder: WorkspaceBuilder,
    detached: bool,
    append: bool,
    answer_yes: bool,
    cli_colors: Colors,
    here: bool = False,
    pre_attach_hook: t.Callable[[], None] | None = None,
    on_error_hook: t.Callable[[], None] | None = None,
    pre_prompt_hook: t.Callable[[], None] | None = None,
) -> Session | None:
    """Dispatch the build to the correct load path and handle errors.

    Handles the detached/attached/append switching logic and the
    ``TmuxpException`` error-recovery prompt.  Extracted so the
    spinner-enabled and spinner-disabled paths share one implementation.

    Parameters
    ----------
    builder : WorkspaceBuilder
        Configured workspace builder.
    detached : bool
        Load session in detached state.
    append : bool
        Append windows to the current session.
    answer_yes : bool
        Skip interactive prompts.
    cli_colors : Colors
        Colors instance for styled output.
    here : bool
        Use current window for first workspace window.
    pre_attach_hook : callable, optional
        Called before attach/switch_client (e.g. stop spinner).
    on_error_hook : callable, optional
        Called before showing the error-recovery prompt (e.g. stop spinner).
    pre_prompt_hook : callable, optional
        Called before any interactive prompt (e.g. stop spinner so ANSI
        escape sequences don't garble the terminal during user input).

    Returns
    -------
    Session | None
        The built session, or ``None`` if the user killed it on error.

    Examples
    --------
    >>> from tmuxp.cli.load import _dispatch_build
    >>> callable(_dispatch_build)
    True
    """
    try:
        if detached:
            _load_detached(builder, cli_colors, pre_output_hook=pre_attach_hook)
            return _setup_plugins(builder)

        if here:
            if "TMUX" in os.environ:  # tmuxp ran from inside tmux
                _load_here_in_current_session(builder)
            else:
                _load_attached(builder, detached, pre_attach_hook=pre_attach_hook)

            return _setup_plugins(builder)

        if append:
            if "TMUX" in os.environ:  # tmuxp ran from inside tmux
                _load_append_windows_to_current_session(builder)
            else:
                _load_attached(builder, detached, pre_attach_hook=pre_attach_hook)

            return _setup_plugins(builder)

        # append and answer_yes have no meaning if specified together
        if answer_yes:
            _load_attached(builder, detached, pre_attach_hook=pre_attach_hook)
            return _setup_plugins(builder)

        if "TMUX" in os.environ:  # tmuxp ran from inside tmux
            if pre_prompt_hook is not None:
                pre_prompt_hook()
            msg = (
                "Already inside TMUX, switch to session? yes/no\n"
                "Or (a)ppend windows in the current active session?\n[y/n/a]"
            )
            options = ["y", "n", "a"]
            choice = prompt_choices(msg, choices=options, color_mode=cli_colors.mode)

            if choice == "y":
                _load_attached(builder, detached, pre_attach_hook=pre_attach_hook)
            elif choice == "a":
                _load_append_windows_to_current_session(builder)
            else:
                _load_detached(builder, cli_colors)
        else:
            _load_attached(builder, detached, pre_attach_hook=pre_attach_hook)

    except exc.TmuxpException as e:
        if on_error_hook is not None:
            on_error_hook()
        logger.debug("workspace build failed", exc_info=True)
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
                logger.info("session killed by user after build error")
        elif choice == "a":
            _reattach(builder, cli_colors)
        else:
            sys.exit()
        return None
    finally:
        builder.on_progress = None
        builder.on_before_script = None
        builder.on_script_output = None
        builder.on_build_event = None

    return _setup_plugins(builder)


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
    here: bool = False,
    cli_colors: Colors | None = None,
    progress_format: str | None = None,
    panel_lines: int | None = None,
    no_progress: bool = False,
    no_shell_command_before: bool = False,
    debug: bool = False,
    template_context: dict[str, str] | None = None,
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
    here : bool
       Use current window for first workspace window and rename session.
       Default False.
    cli_colors : Colors, optional
        Colors instance for CLI output formatting. If None, uses AUTO mode.
    progress_format : str, optional
        Spinner format preset name or custom format string with tokens.
    panel_lines : int, optional
        Number of script-output lines shown in the spinner panel.
        Defaults to the :class:`~tmuxp.cli._progress.Spinner` default (3).
        Override via ``TMUXP_PROGRESS_LINES`` environment variable.
    no_progress : bool
        Disable the progress spinner entirely. Default False.
        Also disabled when ``TMUXP_PROGRESS=0``.
    no_shell_command_before : bool
        Strip ``shell_command_before`` from all levels (session, window, pane)
        before building. Default False.
    debug : bool
        Show tmux commands as they execute. Implies no_progress. Default False.
    template_context : dict, optional
        Mapping of variable names to values for ``{{ variable }}`` template
        rendering. Applied to raw file content before YAML/JSON parsing.
        Typically populated from ``--set KEY=VALUE`` CLI arguments.

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

    logger.info(
        "loading workspace",
        extra={"tmux_config_path": str(workspace_file)},
    )
    _progress_disabled = no_progress or debug or os.getenv("TMUXP_PROGRESS", "1") == "0"

    # --debug: attach handler to libtmux logger that shows tmux commands
    _debug_handler: logging.Handler | None = None
    _debug_prev_level: int | None = None
    if debug:
        _debug_handler = _TmuxCommandDebugHandler(cli_colors)
        _debug_handler.setLevel(logging.DEBUG)
        _libtmux_logger = logging.getLogger("libtmux.common")
        _debug_prev_level = _libtmux_logger.level
        _libtmux_logger.setLevel(logging.DEBUG)
        _libtmux_logger.addHandler(_debug_handler)

    def _cleanup_debug() -> None:
        if _debug_handler is not None:
            _ltlog = logging.getLogger("libtmux.common")
            _ltlog.removeHandler(_debug_handler)
            if _debug_prev_level is not None:
                _ltlog.setLevel(_debug_prev_level)

    if _progress_disabled:
        tmuxp_echo(
            cli_colors.info("[Loading]")
            + " "
            + cli_colors.highlight(str(PrivatePath(workspace_file))),
        )

    # ConfigReader allows us to open a yaml or json file as a dict
    try:
        if template_context:
            raw_workspace = (
                config_reader.ConfigReader._from_file(
                    workspace_file,
                    template_context=template_context,
                )
                or {}
            )
        else:
            raw_workspace = config_reader.ConfigReader._from_file(workspace_file) or {}

        # shapes workspaces relative to config / profile file location
        expanded_workspace = loader.expand(
            raw_workspace,
            cwd=os.path.dirname(workspace_file),
        )
    except Exception:
        _cleanup_debug()
        raise

    # Overridden session name
    if new_session_name:
        expanded_workspace["session_name"] = new_session_name

    # Strip shell_command_before at all levels when --no-shell-command-before
    if no_shell_command_before:
        expanded_workspace.pop("shell_command_before", None)
        for window in expanded_workspace.get("windows", []):
            window.pop("shell_command_before", None)
            for pane in window.get("panes", []):
                pane.pop("shell_command_before", None)

    # Use workspace config values as fallbacks for server connection params
    # (e.g. from tmuxinator cli_args: "-L socket -f tmux.conf")
    if socket_name is None:
        socket_name = expanded_workspace.pop("socket_name", None)
    else:
        expanded_workspace.pop("socket_name", None)
    if socket_path is None:
        socket_path = expanded_workspace.pop("socket_path", None)
    else:
        expanded_workspace.pop("socket_path", None)
    if tmux_config_file is None:
        tmux_config_file = expanded_workspace.pop("config", None)
    else:
        expanded_workspace.pop("config", None)

    # propagate workspace inheritance (e.g. session -> window, window -> pane)
    expanded_workspace = loader.trickle(expanded_workspace)

    t = Server(  # create tmux server object
        socket_name=socket_name,
        socket_path=socket_path,
        config_file=tmux_config_file,
        colors=colors,
    )

    shutil.which("tmux")  # raise exception if tmux not found

    # WorkspaceBuilder creation — outside spinner so plugin prompts are safe
    try:
        builder = WorkspaceBuilder(
            session_config=expanded_workspace,
            plugins=load_plugins(expanded_workspace, colors=cli_colors),
            server=t,
        )
    except exc.EmptyWorkspaceException:
        logger.warning(
            "workspace file is empty",
            extra={"tmux_config_path": str(workspace_file)},
        )
        tmuxp_echo(
            cli_colors.warning("[Warning]")
            + f" {PrivatePath(workspace_file)} is empty or parsed no workspace data",
        )
        _cleanup_debug()
        return None

    session_name = expanded_workspace["session_name"]

    # Session-exists check — outside spinner so prompt_yes_no is safe
    if builder.session_exists(session_name) and not append and not here:
        _confirmed = not detached and (
            answer_yes
            or prompt_yes_no(
                f"{cli_colors.highlight(session_name)} is already running. Attach?",
                default=True,
                color_mode=cli_colors.mode,
            )
        )
        if _confirmed or detached:
            if "on_project_start" in expanded_workspace:
                _hook_cwd = expanded_workspace.get("start_directory")
                util.run_hook_commands(
                    expanded_workspace["on_project_start"],
                    cwd=_hook_cwd,
                )
            # Run on_project_restart hook — fires when reattaching
            if "on_project_restart" in expanded_workspace:
                _hook_cwd = expanded_workspace.get("start_directory")
                util.run_hook_commands(
                    expanded_workspace["on_project_restart"],
                    cwd=_hook_cwd,
                )
        if _confirmed:
            _reattach(builder, cli_colors)
        _cleanup_debug()
        return None

    # Run on_project_start hook — fires before new session build
    if "on_project_start" in expanded_workspace:
        _hook_cwd = expanded_workspace.get("start_directory")
        util.run_hook_commands(
            expanded_workspace["on_project_start"],
            cwd=_hook_cwd,
        )

    if _progress_disabled:
        _private_path = str(PrivatePath(workspace_file))
        result = _dispatch_build(
            builder,
            detached,
            append,
            answer_yes,
            cli_colors,
            here=here,
        )
        if result is not None:
            summary = ""
            try:
                win_count = len(result.windows)
                pane_count = sum(len(w.panes) for w in result.windows)
                summary_parts: list[str] = []
                if win_count:
                    summary_parts.append(f"{win_count} win")
                if pane_count:
                    summary_parts.append(f"{pane_count} panes")
                summary = f"[{', '.join(summary_parts)}]" if summary_parts else ""
            except Exception:
                logger.debug("session gone before summary", exc_info=True)
            ctx = {
                "session": cli_colors.highlight(session_name),
                "workspace_path": cli_colors.info(_private_path),
                "summary": cli_colors.muted(summary) if summary else "",
            }
            checkmark = cli_colors.success("\u2713")
            tmuxp_echo(
                f"{checkmark} {SUCCESS_TEMPLATE.format_map(_SafeFormatMap(ctx))}"
            )
        _cleanup_debug()
        return result

    # Spinner wraps only the actual build phase
    _progress_fmt = resolve_progress_format(
        progress_format
        if progress_format is not None
        else os.getenv("TMUXP_PROGRESS_FORMAT", "default")
    )
    _panel_lines_env = os.getenv("TMUXP_PROGRESS_LINES")
    if _panel_lines_env:
        try:
            _panel_lines_env_int: int | None = int(_panel_lines_env)
        except ValueError:
            _panel_lines_env_int = None
    else:
        _panel_lines_env_int = None
    _panel_lines = panel_lines if panel_lines is not None else _panel_lines_env_int
    _private_path = str(PrivatePath(workspace_file))
    _spinner = Spinner(
        message=(
            f"Loading workspace: {cli_colors.highlight(session_name)} ({_private_path})"
        ),
        color_mode=cli_colors.mode,
        progress_format=_progress_fmt,
        output_lines=_panel_lines if _panel_lines is not None else DEFAULT_OUTPUT_LINES,
        workspace_path=_private_path,
    )
    _success_emitted = False

    def _emit_success() -> None:
        nonlocal _success_emitted
        if _success_emitted:
            return
        _success_emitted = True
        _spinner.success()

    with (
        _silence_stream_handlers(),
        _spinner as spinner,
    ):
        builder.on_build_event = spinner.on_build_event
        _resolved_panel = (
            _panel_lines if _panel_lines is not None else DEFAULT_OUTPUT_LINES
        )
        if _resolved_panel != 0:
            builder.on_script_output = spinner.add_output_line
        result = _dispatch_build(
            builder,
            detached,
            append,
            answer_yes,
            cli_colors,
            here=here,
            pre_attach_hook=_emit_success,
            on_error_hook=spinner.stop,
            pre_prompt_hook=spinner.stop,
        )
        if result is not None:
            _emit_success()
        return result


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
    load_mode_group = parser.add_mutually_exclusive_group()
    load_mode_group.add_argument(
        "-a",
        "--append",
        dest="append",
        action="store_true",
        help="load workspace, appending windows to the current session",
    )
    load_mode_group.add_argument(
        "--here",
        dest="here",
        action="store_true",
        help="use the current window for the first workspace window",
    )
    parser.add_argument(
        "--no-shell-command-before",
        dest="no_shell_command_before",
        action="store_true",
        default=False,
        help="skip shell_command_before at all levels (session, window, pane)",
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

    parser.add_argument(
        "--progress-format",
        metavar="FORMAT",
        dest="progress_format",
        default=None,
        help=(
            "Spinner line format: preset name "
            "(default, minimal, window, pane, verbose) "
            "or a format string with tokens "
            "{session}, {window}, {progress}, {window_progress}, {pane_progress}, etc. "
            "Env: TMUXP_PROGRESS_FORMAT"
        ),
    )

    parser.add_argument(
        "--progress-lines",
        metavar="N",
        dest="panel_lines",
        type=int,
        default=None,
        help=(
            "Number of script-output lines shown in the spinner panel (default: 3). "
            "0 hides the panel entirely (script output goes to stdout). "
            "-1 shows unlimited lines (capped to terminal height). "
            "Env: TMUXP_PROGRESS_LINES"
        ),
    )

    parser.add_argument(
        "--no-progress",
        dest="no_progress",
        action="store_true",
        default=False,
        help=("Disable the animated progress spinner. Env: TMUXP_PROGRESS=0"),
    )

    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="show tmux commands as they execute (implies --no-progress)",
    )

    parser.add_argument(
        "--set",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help=(
            "set template variable for {{ variable }} expressions in workspace config "
            "(repeatable, e.g. --set project=myapp --set port=8080)"
        ),
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
        log.setup_log_file(args.log_file, args.log_level)

    if args.workspace_files is None or len(args.workspace_files) == 0:
        tmuxp_echo(cli_colors.error("Enter at least one config"))
        if parser is not None:
            parser.print_help()
        sys.exit()
        return

    # Parse --set KEY=VALUE args into template context
    template_context: dict[str, str] | None = None
    if args.set:
        template_context = {}
        for item in args.set:
            key, _, value = item.partition("=")
            if not key or not _:
                tmuxp_echo(
                    cli_colors.error("[Error]")
                    + f" Invalid --set format: {item!r} (expected KEY=VALUE)",
                )
                sys.exit(1)
            template_context[key] = value

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
            here=args.here or False,
            cli_colors=cli_colors,
            progress_format=args.progress_format,
            panel_lines=args.panel_lines,
            no_progress=args.no_progress,
            no_shell_command_before=args.no_shell_command_before,
            debug=args.debug,
            template_context=template_context,
        )
