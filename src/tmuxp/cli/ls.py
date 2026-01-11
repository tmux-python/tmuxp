"""CLI for ``tmuxp ls`` subcommand.

List and display workspace configuration files.

Examples
--------
>>> from tmuxp.cli.ls import WorkspaceInfo

Create workspace info from file path:

>>> import pathlib
>>> ws = WorkspaceInfo(
...     name="dev",
...     path="~/.tmuxp/dev.yaml",
...     format="yaml",
...     size=256,
...     mtime="2024-01-15T10:30:00",
...     session_name="development",
...     source="global",
... )
>>> ws["name"]
'dev'
>>> ws["source"]
'global'
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import typing as t

import yaml

from tmuxp._internal.config_reader import ConfigReader
from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace.constants import VALID_WORKSPACE_DIR_FILE_EXTENSIONS
from tmuxp.workspace.finders import (
    find_local_workspace_files,
    get_workspace_dir,
    get_workspace_dir_candidates,
)

from ._colors import Colors, build_description, get_color_mode
from ._output import OutputFormatter, OutputMode, get_output_mode

LS_DESCRIPTION = build_description(
    """
    List workspace files in the tmuxp configuration directory.
    """,
    (
        (
            None,
            [
                "tmuxp ls",
                "tmuxp ls --tree",
                "tmuxp ls --full",
            ],
        ),
        (
            "Machine-readable output examples",
            [
                "tmuxp ls --json",
                "tmuxp ls --json --full",
                "tmuxp ls --ndjson",
                "tmuxp ls --json | jq '.workspaces[].name'",
            ],
        ),
    ),
)

if t.TYPE_CHECKING:
    from typing import TypeAlias

    CLIColorModeLiteral: TypeAlias = t.Literal["auto", "always", "never"]


class WorkspaceInfo(t.TypedDict):
    """Workspace file information for JSON output.

    Attributes
    ----------
    name : str
        Workspace name (file stem without extension).
    path : str
        Path to workspace file (with ~ contraction).
    format : str
        File format (yaml or json).
    size : int
        File size in bytes.
    mtime : str
        Modification time in ISO format.
    session_name : str | None
        Session name from config if parseable.
    source : str
        Source location: "local" (cwd/parents) or "global" (~/.tmuxp/).
    """

    name: str
    path: str
    format: str
    size: int
    mtime: str
    session_name: str | None
    source: str


class CLILsNamespace(argparse.Namespace):
    """Typed :class:`argparse.Namespace` for tmuxp ls command.

    Examples
    --------
    >>> ns = CLILsNamespace()
    >>> ns.color = "auto"
    >>> ns.color
    'auto'
    """

    color: CLIColorModeLiteral
    tree: bool
    output_json: bool
    output_ndjson: bool
    full: bool


def create_ls_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``ls`` subcommand.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser to augment.

    Returns
    -------
    argparse.ArgumentParser
        The augmented parser.

    Examples
    --------
    >>> import argparse
    >>> parser = argparse.ArgumentParser()
    >>> result = create_ls_subparser(parser)
    >>> result is parser
    True
    """
    parser.add_argument(
        "--tree",
        action="store_true",
        help="display workspaces grouped by directory",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="output as JSON",
    )
    parser.add_argument(
        "--ndjson",
        action="store_true",
        dest="output_ndjson",
        help="output as NDJSON (one JSON per line)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="include full config content in output",
    )
    return parser


def _get_workspace_info(
    filepath: pathlib.Path,
    *,
    source: str = "global",
    include_config: bool = False,
) -> dict[str, t.Any]:
    """Extract metadata from a workspace file.

    Parameters
    ----------
    filepath : pathlib.Path
        Path to the workspace file.
    source : str
        Source location: "local" or "global". Default "global".
    include_config : bool
        If True, include full parsed config content. Default False.

    Returns
    -------
    dict[str, Any]
        Workspace metadata dictionary. Includes 'config' key when include_config=True.

    Examples
    --------
    >>> content = "session_name: test-session" + chr(10) + "windows: []"
    >>> yaml_file = tmp_path / "test.yaml"
    >>> _ = yaml_file.write_text(content)
    >>> info = _get_workspace_info(yaml_file)
    >>> info['session_name']
    'test-session'
    >>> info['format']
    'yaml'
    >>> info['source']
    'global'
    >>> info_local = _get_workspace_info(yaml_file, source="local")
    >>> info_local['source']
    'local'
    >>> info_full = _get_workspace_info(yaml_file, include_config=True)
    >>> 'config' in info_full
    True
    >>> info_full['config']['session_name']
    'test-session'
    """
    stat = filepath.stat()
    ext = filepath.suffix.lower()
    file_format = "json" if ext == ".json" else "yaml"

    # Try to extract session_name and optionally full config
    session_name: str | None = None
    config_content: dict[str, t.Any] | None = None
    try:
        config = ConfigReader.from_file(filepath)
        if isinstance(config.content, dict):
            session_name = config.content.get("session_name")
            if include_config:
                config_content = config.content
    except (yaml.YAMLError, json.JSONDecodeError, OSError):
        # If we can't parse it, just skip session_name
        pass

    result: dict[str, t.Any] = {
        "name": filepath.stem,
        "path": str(PrivatePath(filepath)),
        "format": file_format,
        "size": stat.st_size,
        "mtime": datetime.datetime.fromtimestamp(
            stat.st_mtime,
            tz=datetime.timezone.utc,
        ).isoformat(),
        "session_name": session_name,
        "source": source,
    }

    if include_config:
        result["config"] = config_content

    return result


def _render_config_tree(config: dict[str, t.Any], colors: Colors) -> list[str]:
    """Render config windows/panes as tree lines for human output.

    Parameters
    ----------
    config : dict[str, Any]
        Parsed config content.
    colors : Colors
        Color manager.

    Returns
    -------
    list[str]
        Lines of formatted tree output.

    Examples
    --------
    >>> from tmuxp.cli._colors import ColorMode, Colors
    >>> colors = Colors(ColorMode.NEVER)
    >>> config = {
    ...     "session_name": "dev",
    ...     "windows": [
    ...         {"window_name": "editor", "layout": "main-horizontal"},
    ...         {"window_name": "shell"},
    ...     ],
    ... }
    >>> lines = _render_config_tree(config, colors)
    >>> "editor" in lines[0]
    True
    >>> "shell" in lines[1]
    True
    """
    lines: list[str] = []
    windows = config.get("windows", [])

    for i, window in enumerate(windows):
        if not isinstance(window, dict):
            continue

        is_last_window = i == len(windows) - 1
        prefix = "└── " if is_last_window else "├── "
        child_prefix = "    " if is_last_window else "│   "

        # Window line
        window_name = window.get("window_name", f"window {i}")
        layout = window.get("layout", "")
        layout_info = f" [{layout}]" if layout else ""
        lines.append(f"{prefix}{colors.info(window_name)}{colors.muted(layout_info)}")

        # Panes
        panes = window.get("panes", [])
        for j, pane in enumerate(panes):
            is_last_pane = j == len(panes) - 1
            pane_prefix = "└── " if is_last_pane else "├── "

            # Get pane command summary
            if isinstance(pane, dict):
                cmds = pane.get("shell_command", [])
                if isinstance(cmds, str):
                    cmd_str = cmds
                elif isinstance(cmds, list) and cmds:
                    cmd_str = str(cmds[0])
                else:
                    cmd_str = ""
            elif isinstance(pane, str):
                cmd_str = pane
            else:
                cmd_str = ""

            # Truncate long commands
            if len(cmd_str) > 40:
                cmd_str = cmd_str[:37] + "..."

            pane_info = f": {cmd_str}" if cmd_str else ""
            lines.append(
                f"{child_prefix}{pane_prefix}{colors.muted(f'pane {j}')}{pane_info}"
            )

    return lines


def _render_global_workspace_dirs(
    formatter: OutputFormatter,
    colors: Colors,
    global_dir_candidates: list[dict[str, t.Any]],
) -> None:
    """Render global workspace directories section.

    Parameters
    ----------
    formatter : OutputFormatter
        Output formatter.
    colors : Colors
        Color manager.
    global_dir_candidates : list[dict[str, Any]]
        List of global workspace directory candidates with metadata.

    Examples
    --------
    >>> from tmuxp.cli._output import OutputFormatter, OutputMode
    >>> from tmuxp.cli._colors import Colors, ColorMode
    >>> formatter = OutputFormatter(OutputMode.HUMAN)
    >>> colors = Colors(ColorMode.NEVER)
    >>> candidates = [
    ...     {"path": "~/.tmuxp", "source": "Legacy", "exists": True,
    ...      "workspace_count": 5, "active": True},
    ...     {"path": "~/.config/tmuxp", "source": "XDG", "exists": False,
    ...      "workspace_count": 0, "active": False},
    ... ]
    >>> _render_global_workspace_dirs(formatter, colors, candidates)
    <BLANKLINE>
    Global workspace directories:
      Legacy: ~/.tmuxp (5 workspaces, active)
      XDG: ~/.config/tmuxp (not found)
    """
    formatter.emit_text("")
    formatter.emit_text(colors.heading("Global workspace directories:"))
    for candidate in global_dir_candidates:
        path = candidate["path"]
        source = candidate.get("source", "")
        source_prefix = f"{source}: " if source else ""
        if candidate["exists"]:
            count = candidate["workspace_count"]
            status = f"{count} workspace{'s' if count != 1 else ''}"
            if candidate["active"]:
                status += ", active"
                formatter.emit_text(
                    f"  {colors.muted(source_prefix)}{colors.info(path)} "
                    f"({colors.success(status)})"
                )
            else:
                formatter.emit_text(
                    f"  {colors.muted(source_prefix)}{colors.info(path)} ({status})"
                )
        else:
            formatter.emit_text(
                f"  {colors.muted(source_prefix)}{colors.info(path)} "
                f"({colors.muted('not found')})"
            )


def _output_flat(
    workspaces: list[dict[str, t.Any]],
    formatter: OutputFormatter,
    colors: Colors,
    *,
    full: bool = False,
    global_dir_candidates: list[dict[str, t.Any]] | None = None,
) -> None:
    """Output workspaces in flat list format.

    Groups workspaces by source (local vs global) for human output.

    Parameters
    ----------
    workspaces : list[dict[str, Any]]
        Workspaces to display.
    formatter : OutputFormatter
        Output formatter.
    colors : Colors
        Color manager.
    full : bool
        If True, show full config details in tree format. Default False.
    global_dir_candidates : list[dict[str, Any]] | None
        List of global workspace directory candidates with metadata.

    Examples
    --------
    >>> from tmuxp.cli._output import OutputFormatter, OutputMode
    >>> from tmuxp.cli._colors import Colors, ColorMode
    >>> formatter = OutputFormatter(OutputMode.HUMAN)
    >>> colors = Colors(ColorMode.NEVER)
    >>> workspaces = [{"name": "dev", "path": "~/.tmuxp/dev.yaml", "source": "global"}]
    >>> _output_flat(workspaces, formatter, colors)
    Global workspaces:
      dev
    """
    # Separate by source for human output grouping
    local_workspaces = [ws for ws in workspaces if ws["source"] == "local"]
    global_workspaces = [ws for ws in workspaces if ws["source"] == "global"]

    def output_workspace(ws: dict[str, t.Any], show_path: bool) -> None:
        """Output a single workspace."""
        formatter.emit(ws)
        path_info = f"  {colors.info(ws['path'])}" if show_path else ""
        formatter.emit_text(f"  {colors.highlight(ws['name'])}{path_info}")

        # With --full, show config tree
        if full and ws.get("config"):
            for line in _render_config_tree(ws["config"], colors):
                formatter.emit_text(f"    {line}")

    # Output local workspaces first (closest to user's context)
    if local_workspaces:
        formatter.emit_text(colors.heading("Local workspaces:"))
        for ws in local_workspaces:
            output_workspace(ws, show_path=True)

    # Output global workspaces with active directory in header
    if global_workspaces:
        if local_workspaces:
            formatter.emit_text("")  # Blank line separator

        # Find active directory for header
        active_dir = ""
        if global_dir_candidates:
            for candidate in global_dir_candidates:
                if candidate["active"]:
                    active_dir = candidate["path"]
                    break

        if active_dir:
            formatter.emit_text(colors.heading(f"Global workspaces ({active_dir}):"))
        else:
            formatter.emit_text(colors.heading("Global workspaces:"))

        for ws in global_workspaces:
            output_workspace(ws, show_path=False)

    # Output global workspace directories section
    if global_dir_candidates:
        _render_global_workspace_dirs(formatter, colors, global_dir_candidates)


def _output_tree(
    workspaces: list[dict[str, t.Any]],
    formatter: OutputFormatter,
    colors: Colors,
    *,
    full: bool = False,
    global_dir_candidates: list[dict[str, t.Any]] | None = None,
) -> None:
    """Output workspaces grouped by directory (tree view).

    Parameters
    ----------
    workspaces : list[dict[str, Any]]
        Workspaces to display.
    formatter : OutputFormatter
        Output formatter.
    colors : Colors
        Color manager.
    full : bool
        If True, show full config details in tree format. Default False.
    global_dir_candidates : list[dict[str, Any]] | None
        List of global workspace directory candidates with metadata.

    Examples
    --------
    >>> from tmuxp.cli._output import OutputFormatter, OutputMode
    >>> from tmuxp.cli._colors import Colors, ColorMode
    >>> formatter = OutputFormatter(OutputMode.HUMAN)
    >>> colors = Colors(ColorMode.NEVER)
    >>> workspaces = [{"name": "dev", "path": "~/.tmuxp/dev.yaml", "source": "global"}]
    >>> _output_tree(workspaces, formatter, colors)
    <BLANKLINE>
    ~/.tmuxp
      dev
    """
    # Group by parent directory
    by_directory: dict[str, list[dict[str, t.Any]]] = {}
    for ws in workspaces:
        # Extract parent directory from path
        parent = str(pathlib.Path(ws["path"]).parent)
        by_directory.setdefault(parent, []).append(ws)

    # Output grouped
    for directory in sorted(by_directory.keys()):
        dir_workspaces = by_directory[directory]

        # Human output: directory header
        formatter.emit_text(f"\n{colors.highlight(directory)}")

        for ws in dir_workspaces:
            # JSON/NDJSON output
            formatter.emit(ws)

            # Human output: indented workspace name
            ws_name = ws["name"]
            ws_session = ws.get("session_name")
            session_info = ""
            if ws_session and ws_session != ws_name:
                session_info = f" {colors.muted(f'→ {ws_session}')}"
            formatter.emit_text(f"  {colors.highlight(ws_name)}{session_info}")

            # With --full, show config tree
            if full and ws.get("config"):
                for line in _render_config_tree(ws["config"], colors):
                    formatter.emit_text(f"    {line}")

    # Output global workspace directories section
    if global_dir_candidates:
        _render_global_workspace_dirs(formatter, colors, global_dir_candidates)


def command_ls(
    args: CLILsNamespace | None = None,
    parser: argparse.ArgumentParser | None = None,
) -> None:
    """Entrypoint for ``tmuxp ls`` subcommand.

    Lists both local workspaces (from cwd and parent directories) and
    global workspaces (from ~/.tmuxp/).

    Parameters
    ----------
    args : CLILsNamespace | None
        Parsed command-line arguments.
    parser : argparse.ArgumentParser | None
        The argument parser (unused but required by CLI interface).

    Examples
    --------
    >>> # command_ls() lists workspaces from cwd/parents and ~/.tmuxp/
    """
    import json
    import sys

    # Get color mode from args or default to AUTO
    color_mode = get_color_mode(args.color if args else None)
    colors = Colors(color_mode)

    # Determine output mode and options
    output_json = args.output_json if args else False
    output_ndjson = args.output_ndjson if args else False
    tree = args.tree if args else False
    full = args.full if args else False
    output_mode = get_output_mode(output_json, output_ndjson)
    formatter = OutputFormatter(output_mode)

    # Get global workspace directory candidates
    global_dir_candidates = get_workspace_dir_candidates()

    # 1. Collect local workspace files (cwd and parents)
    local_files = find_local_workspace_files()
    workspaces: list[dict[str, t.Any]] = [
        _get_workspace_info(f, source="local", include_config=full) for f in local_files
    ]

    # 2. Collect global workspace files (~/.tmuxp/)
    tmuxp_dir = pathlib.Path(get_workspace_dir())
    if tmuxp_dir.exists() and tmuxp_dir.is_dir():
        workspaces.extend(
            _get_workspace_info(f, source="global", include_config=full)
            for f in sorted(tmuxp_dir.iterdir())
            if not f.is_dir()
            and f.suffix.lower() in VALID_WORKSPACE_DIR_FILE_EXTENSIONS
        )

    if not workspaces:
        formatter.emit_text(colors.warning("No workspaces found."))
        # Still show global workspace directories even with no workspaces
        if output_mode == OutputMode.HUMAN:
            _render_global_workspace_dirs(formatter, colors, global_dir_candidates)
        elif output_mode == OutputMode.JSON:
            # Output structured JSON with empty workspaces
            output_data = {
                "workspaces": [],
                "global_workspace_dirs": global_dir_candidates,
            }
            sys.stdout.write(json.dumps(output_data, indent=2) + "\n")
            sys.stdout.flush()
        # NDJSON: just output nothing for empty workspaces
        return

    # JSON mode: output structured object instead of using formatter
    if output_mode == OutputMode.JSON:
        output_data = {
            "workspaces": workspaces,
            "global_workspace_dirs": global_dir_candidates,
        }
        sys.stdout.write(json.dumps(output_data, indent=2) + "\n")
        sys.stdout.flush()
        return

    # Human and NDJSON output
    if tree:
        _output_tree(
            workspaces,
            formatter,
            colors,
            full=full,
            global_dir_candidates=global_dir_candidates,
        )
    else:
        _output_flat(
            workspaces,
            formatter,
            colors,
            full=full,
            global_dir_candidates=global_dir_candidates,
        )

    formatter.finalize()
