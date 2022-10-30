import logging
import os
import typing as t

from colorama import Fore

from tmuxp.cli.utils import tmuxp_echo
from tmuxp.types import StrPath
from tmuxp.workspace.constants import VALID_WORKSPACE_DIR_FILE_EXTENSIONS

logger = logging.getLogger(__name__)


def is_workspace_file(filename, extensions=[".yml", ".yaml", ".json"]):
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
    extensions = [extensions] if isinstance(extensions, str) else extensions
    return any(filename.endswith(e) for e in extensions)


def in_dir(
    workspace_dir=os.path.expanduser("~/.tmuxp"), extensions=[".yml", ".yaml", ".json"]
):
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
    workspace_files = []

    for filename in os.listdir(workspace_dir):
        if is_workspace_file(filename, extensions) and not filename.startswith("."):
            workspace_files.append(filename)

    return workspace_files


def in_cwd():
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
    workspace_files = []

    for filename in os.listdir(os.getcwd()):
        if filename.startswith(".tmuxp") and is_workspace_file(filename):
            workspace_files.append(filename)

    return workspace_files


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


def find_workspace_file(
    workspace_file: StrPath,
    workspace_dir: t.Optional[StrPath] = None,
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
        workspace file, valid examples:

        - a file name, my_workspace.yaml
        - relative path, ../my_workspace.yaml or ../project
        - a period, .
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
        or workspace_file == "."
        or workspace_file == ""
        or workspace_file == "./"
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
            if not len(candidates):
                file_error = (
                    "workspace-file not found in workspace dir (yaml/yml/json) %s "
                    "for name" % (workspace_dir)
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
                tmuxp_echo(
                    Fore.RED
                    + "Multiple .tmuxp.{yml,yaml,json} workspace_files in %s"
                    % dirname(workspace_file)
                    + Fore.RESET
                )
                tmuxp_echo(
                    "This is undefined behavior, use only one. "
                    "Use file names e.g. myproject.json, coolproject.yaml. "
                    "You can load them by filename."
                )
            elif not len(candidates):
                file_error = "No tmuxp files found in directory"
        if len(candidates):
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
        and path != "."
        and path != ""
    )
