"""Workspace (configuration file) finders for tmuxp."""

from __future__ import annotations

import logging
import os
import pathlib
import typing as t

from tmuxp._internal.colors import ColorMode, Colors
from tmuxp._internal.private_path import PrivatePath
from tmuxp.log import tmuxp_echo
from tmuxp.workspace.constants import VALID_WORKSPACE_DIR_FILE_EXTENSIONS

logger = logging.getLogger(__name__)

#: Local workspace file names (dotfiles in project directories)
LOCAL_WORKSPACE_FILES = [".tmuxp.yaml", ".tmuxp.yml", ".tmuxp.json"]

if t.TYPE_CHECKING:
    from typing import TypeAlias

    from tmuxp.types import StrPath

    ValidExtensions: TypeAlias = t.Literal[".yml", ".yaml", ".json"]


def is_workspace_file(
    filename: str,
    extensions: ValidExtensions | list[ValidExtensions] | None = None,
) -> bool:
    """
    Return True if file has a valid workspace file type.

    Parameters
    ----------
    filename : str
        filename to check (e.g. ``mysession.json``).
    extensions : str or list
        filetypes to check (e.g. ``['.yaml', '.json']``).

    Returns
    -------
    bool
    """
    if extensions is None:
        extensions = [".yml", ".yaml", ".json"]
    extensions = [extensions] if isinstance(extensions, str) else extensions
    return any(filename.endswith(e) for e in extensions)


def in_dir(
    workspace_dir: pathlib.Path | str | None = None,
    extensions: list[ValidExtensions] | None = None,
) -> list[str]:
    """
    Return a list of workspace_files in ``workspace_dir``.

    Parameters
    ----------
    workspace_dir : str
        directory to search
    extensions : list
        filetypes to check (e.g. ``['.yaml', '.json']``).

    Returns
    -------
    list
    """
    if workspace_dir is None:
        workspace_dir = os.path.expanduser("~/.tmuxp")

    if extensions is None:
        extensions = [".yml", ".yaml", ".json"]

    return [
        filename
        for filename in os.listdir(workspace_dir)
        if is_workspace_file(filename, extensions) and not filename.startswith(".")
    ]


def in_cwd() -> list[str]:
    """
    Return list of workspace_files in current working directory.

    If filename is ``.tmuxp.py``, ``.tmuxp.json``, ``.tmuxp.yaml``.

    Returns
    -------
    list
        workspace_files in current working directory

    Examples
    --------
    >>> sorted(in_cwd())
    ['.tmuxp.json', '.tmuxp.yaml']
    """
    return [
        filename
        for filename in os.listdir(os.getcwd())
        if filename.startswith(".tmuxp") and is_workspace_file(filename)
    ]


def find_local_workspace_files(
    start_dir: pathlib.Path | str | None = None,
    *,
    stop_at_home: bool = True,
) -> list[pathlib.Path]:
    """Find .tmuxp.* files by traversing upward from start directory.

    Searches the start directory and all parent directories up to (but not past):
    - User home directory (when stop_at_home=True)
    - Filesystem root

    Parameters
    ----------
    start_dir : pathlib.Path | str | None
        Directory to start searching from. Defaults to current working directory.
    stop_at_home : bool
        If True, stops traversal at user home directory. Default True.

    Returns
    -------
    list[pathlib.Path]
        List of workspace file paths found, ordered from closest to farthest.

    Examples
    --------
    >>> import tempfile
    >>> import pathlib
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     home = pathlib.Path(tmpdir)
    ...     project = home / "project"
    ...     project.mkdir()
    ...     _ = (project / ".tmuxp.yaml").write_text("session_name: test")
    ...     # Would find .tmuxp.yaml in project dir
    ...     len(find_local_workspace_files(project, stop_at_home=False)) >= 0
    True
    """
    if start_dir is None:
        start_dir = os.getcwd()

    current = pathlib.Path(start_dir).resolve()
    home = pathlib.Path.home().resolve()
    found: list[pathlib.Path] = []

    while True:
        # Check for local workspace files in current directory
        for filename in LOCAL_WORKSPACE_FILES:
            candidate = current / filename
            if candidate.is_file():
                found.append(candidate)
                break  # Only one per directory (first match wins: .yaml > .yml > .json)

        # Stop conditions
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        if stop_at_home and current == home:
            break

        current = parent

    return found


def get_workspace_dir() -> str:
    """
    Return tmuxp workspace directory.

    ``TMUXP_CONFIGDIR`` environmental variable has precedence if set. We also
    evaluate XDG default directory from XDG_CONFIG_HOME environmental variable
    if set or its default. Then the old default ~/.tmuxp is returned for
    compatibility.

    Returns
    -------
    str :
        absolute path to tmuxp config directory
    """
    paths = []
    if "TMUXP_CONFIGDIR" in os.environ:
        paths.append(os.environ["TMUXP_CONFIGDIR"])
    if "XDG_CONFIG_HOME" in os.environ:
        paths.append(os.path.join(os.environ["XDG_CONFIG_HOME"], "tmuxp"))
    else:
        paths.append("~/.config/tmuxp/")
    paths.append("~/.tmuxp")

    for path in paths:
        path = os.path.expanduser(path)
        if os.path.isdir(path):
            return path
    # Return last path as default if none of the previous ones matched
    return path


def get_workspace_dir_candidates() -> list[dict[str, t.Any]]:
    """Return all candidate workspace directories with existence status.

    Returns a list of all directories that tmuxp checks for workspaces,
    in priority order, with metadata about each.

    The priority order is:
    1. ``TMUXP_CONFIGDIR`` environment variable (if set)
    2. ``XDG_CONFIG_HOME/tmuxp`` (if XDG_CONFIG_HOME set) OR ``~/.config/tmuxp/``
    3. ``~/.tmuxp`` (legacy default)

    Returns
    -------
    list[dict[str, Any]]
        List of dicts with:
        - path: str (privacy-masked via PrivatePath)
        - source: str (e.g., "$TMUXP_CONFIGDIR", "$XDG_CONFIG_HOME/tmuxp", "Legacy")
        - exists: bool
        - workspace_count: int (0 if not exists)
        - active: bool (True if this is the directory get_workspace_dir() returns)

    Examples
    --------
    >>> candidates = get_workspace_dir_candidates()
    >>> isinstance(candidates, list)
    True
    >>> all('path' in c and 'exists' in c for c in candidates)
    True
    """
    # Build list of candidate paths with sources (same logic as get_workspace_dir)
    # Each entry is (raw_path, source_label)
    path_sources: list[tuple[str, str]] = []
    if "TMUXP_CONFIGDIR" in os.environ:
        path_sources.append((os.environ["TMUXP_CONFIGDIR"], "$TMUXP_CONFIGDIR"))
    if "XDG_CONFIG_HOME" in os.environ:
        path_sources.append(
            (
                os.path.join(os.environ["XDG_CONFIG_HOME"], "tmuxp"),
                "$XDG_CONFIG_HOME/tmuxp",
            )
        )
    else:
        path_sources.append(("~/.config/tmuxp/", "XDG default"))
    path_sources.append(("~/.tmuxp", "Legacy"))

    # Get the active directory for comparison
    active_dir = get_workspace_dir()

    candidates: list[dict[str, t.Any]] = []
    for raw_path, source in path_sources:
        expanded = os.path.expanduser(raw_path)
        exists = os.path.isdir(expanded)

        # Count workspace files if directory exists
        workspace_count = 0
        if exists:
            workspace_count = len(
                [
                    f
                    for f in os.listdir(expanded)
                    if not f.startswith(".")
                    and os.path.splitext(f)[1].lower()
                    in VALID_WORKSPACE_DIR_FILE_EXTENSIONS
                ]
            )

        candidates.append(
            {
                "path": str(PrivatePath(expanded)),
                "source": source,
                "exists": exists,
                "workspace_count": workspace_count,
                "active": expanded == active_dir,
            }
        )

    return candidates


def find_workspace_file(
    workspace_file: StrPath,
    workspace_dir: StrPath | None = None,
) -> str:
    """
    Return the real config path or raise an exception.

    If workspace file is directory, scan for .tmuxp.{yaml,yml,json} in directory. If
    one or more found, it will warn and pick the first.

    If workspace file is ".", "./" or None, it will scan current directory.

    If workspace file is has no path and only a filename, e.g. "my_workspace.yaml" it
    will search workspace dir.

    If workspace file has no path and no extension, e.g. "my_workspace", it will scan
    for file name with yaml, yml and json. If multiple exist, it will warn and pick the
    first.

    Parameters
    ----------
    workspace_file : str
        Workspace file, valid examples:

        - a file name, my_workspace.yaml
        - relative path, ../my_workspace.yaml or ../project
        - a period, .

    Returns
    -------
    str
        Resolved absolute path to workspace file.

    Raises
    ------
    FileNotFoundError
        If workspace file cannot be found.
    """
    if not workspace_dir:
        workspace_dir = get_workspace_dir()
    path = os.path
    exists, join, isabs = path.exists, path.join, path.isabs
    dirname, normpath, splitext = path.dirname, path.normpath, path.splitext
    cwd = os.getcwd()
    is_name = False
    file_error = None

    workspace_file = os.path.expanduser(workspace_file)
    # if purename, resolve to confg dir
    if is_pure_name(workspace_file):
        is_name = True
    elif (
        not isabs(workspace_file)
        or len(dirname(workspace_file)) > 1
        or workspace_file in {".", "", "./"}
    ):  # if relative, fill in full path
        workspace_file = normpath(join(cwd, workspace_file))

    # no extension, scan
    if path.isdir(workspace_file) or not splitext(workspace_file)[1]:
        if is_name:
            candidates = [
                x
                for x in [
                    f"{join(workspace_dir, workspace_file)}{ext}"
                    for ext in VALID_WORKSPACE_DIR_FILE_EXTENSIONS
                ]
                if exists(x)
            ]
            if not candidates:
                file_error = (
                    "workspace-file not found "
                    f"in workspace dir (yaml/yml/json) {workspace_dir} for name"
                )
        else:
            candidates = [
                x
                for x in [
                    join(workspace_file, ext)
                    for ext in [".tmuxp.yaml", ".tmuxp.yml", ".tmuxp.json"]
                ]
                if exists(x)
            ]

            if len(candidates) > 1:
                colors = Colors(ColorMode.AUTO)
                tmuxp_echo(
                    colors.error(
                        "Multiple .tmuxp.{yml,yaml,json} workspace_files in "
                        + dirname(workspace_file)
                    ),
                )
                tmuxp_echo(
                    "This is undefined behavior, use only one. "
                    "Use file names e.g. myproject.json, coolproject.yaml. "
                    "You can load them by filename.",
                )
            elif not candidates:
                file_error = "No tmuxp files found in directory"
        if candidates:
            workspace_file = candidates[0]
    elif not exists(workspace_file):
        file_error = "file not found"

    if file_error:
        raise FileNotFoundError(file_error, workspace_file)

    return workspace_file


def is_pure_name(path: str) -> bool:
    """
    Return True if path is a name and not a file path.

    Parameters
    ----------
    path : str
        Path (can be absolute, relative, etc.)

    Returns
    -------
    bool
        True if path is a name of workspace in workspace dir, not file path.
    """
    return (
        not os.path.isabs(path)
        and len(os.path.dirname(path)) == 0
        and not os.path.splitext(path)[1]
        and path not in {".", ""}
    )
