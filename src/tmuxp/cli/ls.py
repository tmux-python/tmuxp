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
import pathlib
import typing as t

from tmuxp._internal.config_reader import ConfigReader
from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace.constants import VALID_WORKSPACE_DIR_FILE_EXTENSIONS
from tmuxp.workspace.finders import find_local_workspace_files, get_workspace_dir

from ._colors import Colors, build_description, get_color_mode
from ._output import OutputFormatter, get_output_mode

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
            ],
        ),
        (
            "Machine-readable output:",
            [
                "tmuxp ls --json",
                "tmuxp ls --ndjson",
                "tmuxp ls --json | jq '.[] | .name'",
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
    return parser


def _get_workspace_info(
    filepath: pathlib.Path,
    *,
    source: str = "global",
) -> WorkspaceInfo:
    """Extract metadata from a workspace file.

    Parameters
    ----------
    filepath : pathlib.Path
        Path to the workspace file.
    source : str
        Source location: "local" or "global". Default "global".

    Returns
    -------
    WorkspaceInfo
        Workspace metadata dictionary.

    Examples
    --------
    >>> import tempfile
    >>> import pathlib
    >>> content = "session_name: test-session" + chr(10) + "windows: []"
    >>> with tempfile.NamedTemporaryFile(
    ...     suffix='.yaml', delete=False, mode='w'
    ... ) as f:
    ...     _ = f.write(content)
    ...     temp_path = pathlib.Path(f.name)
    >>> info = _get_workspace_info(temp_path)
    >>> info['session_name']
    'test-session'
    >>> info['format']
    'yaml'
    >>> info['source']
    'global'
    >>> info_local = _get_workspace_info(temp_path, source="local")
    >>> info_local['source']
    'local'
    >>> temp_path.unlink()
    """
    stat = filepath.stat()
    ext = filepath.suffix.lower()
    file_format = "json" if ext == ".json" else "yaml"

    # Try to extract session_name from config
    session_name: str | None = None
    try:
        config = ConfigReader.from_file(filepath)
        if isinstance(config.content, dict):
            session_name = config.content.get("session_name")
    except Exception:
        # If we can't parse it, just skip session_name
        pass

    return WorkspaceInfo(
        name=filepath.stem,
        path=str(PrivatePath(filepath)),
        format=file_format,
        size=stat.st_size,
        mtime=datetime.datetime.fromtimestamp(
            stat.st_mtime,
            tz=datetime.timezone.utc,
        ).isoformat(),
        session_name=session_name,
        source=source,
    )


def _output_flat(
    workspaces: list[WorkspaceInfo],
    formatter: OutputFormatter,
    colors: Colors,
) -> None:
    """Output workspaces in flat list format.

    Groups workspaces by source (local vs global) for human output.

    Parameters
    ----------
    workspaces : list[WorkspaceInfo]
        Workspaces to display.
    formatter : OutputFormatter
        Output formatter.
    colors : Colors
        Color manager.
    """
    # Separate by source for human output grouping
    local_workspaces = [ws for ws in workspaces if ws["source"] == "local"]
    global_workspaces = [ws for ws in workspaces if ws["source"] == "global"]

    # Output local workspaces first (closest to user's context)
    if local_workspaces:
        formatter.emit_text(colors.muted("Local workspaces:"))
        for ws in local_workspaces:
            formatter.emit(dict(ws))
            formatter.emit_text(
                f"  {colors.info(ws['name'])}  {colors.muted(ws['path'])}"
            )

    # Output global workspaces
    if global_workspaces:
        if local_workspaces:
            formatter.emit_text("")  # Blank line separator
        formatter.emit_text(colors.muted("Global workspaces:"))
        for ws in global_workspaces:
            formatter.emit(dict(ws))
            formatter.emit_text(f"  {colors.info(ws['name'])}")


def _output_tree(
    workspaces: list[WorkspaceInfo],
    formatter: OutputFormatter,
    colors: Colors,
) -> None:
    """Output workspaces grouped by directory (tree view).

    Parameters
    ----------
    workspaces : list[WorkspaceInfo]
        Workspaces to display.
    formatter : OutputFormatter
        Output formatter.
    colors : Colors
        Color manager.
    """
    # Group by parent directory
    by_directory: dict[str, list[WorkspaceInfo]] = {}
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
            formatter.emit(dict(ws))

            # Human output: indented workspace name
            ws_name = ws["name"]
            ws_session = ws["session_name"]
            session_info = ""
            if ws_session and ws_session != ws_name:
                session_info = f" {colors.muted(f'→ {ws_session}')}"
            formatter.emit_text(f"  {colors.info(ws_name)}{session_info}")


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
    # Get color mode from args or default to AUTO
    color_mode = get_color_mode(args.color if args else None)
    colors = Colors(color_mode)

    # Determine output mode
    output_json = args.output_json if args else False
    output_ndjson = args.output_ndjson if args else False
    tree = args.tree if args else False
    output_mode = get_output_mode(output_json, output_ndjson)
    formatter = OutputFormatter(output_mode)

    # 1. Collect local workspace files (cwd and parents)
    local_files = find_local_workspace_files()
    workspaces: list[WorkspaceInfo] = [
        _get_workspace_info(f, source="local") for f in local_files
    ]

    # 2. Collect global workspace files (~/.tmuxp/)
    tmuxp_dir = pathlib.Path(get_workspace_dir())
    if tmuxp_dir.exists() and tmuxp_dir.is_dir():
        workspaces.extend(
            _get_workspace_info(f, source="global")
            for f in sorted(tmuxp_dir.iterdir())
            if not f.is_dir()
            and f.suffix.lower() in VALID_WORKSPACE_DIR_FILE_EXTENSIONS
        )

    if not workspaces:
        formatter.emit_text(colors.warning("No workspaces found."))
        formatter.finalize()
        return

    # Output based on mode
    if tree:
        _output_tree(workspaces, formatter, colors)
    else:
        _output_flat(workspaces, formatter, colors)

    formatter.finalize()
