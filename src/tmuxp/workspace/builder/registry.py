"""Resolve and sandbox workspace builders selected by a workspace config.

A workspace may point tmuxp at a builder other than the classic
:class:`tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder` via the
``workspace_builder`` key (a Python dotted path, ``module:attr`` reference, or
an entry-point name in the ``tmuxp.workspace_builders`` group). When the builder
lives outside the active environment, ``workspace_builder_paths`` lists trusted
directories that are temporarily added to ``sys.path`` for the import and build.

Security note: only literal directories are prepended to ``sys.path``. This
deliberately avoids :func:`site.addsitedir`, which executes ``.pth`` startup
files and is broader than making a module importable. The trust boundary is the
author of the workspace file.
"""

from __future__ import annotations

import contextlib
import importlib
import inspect
import os
import pathlib
import sys
import typing as t
from importlib import metadata

from tmuxp import exc
from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder
from tmuxp.workspace.loader import expandshell

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from tmuxp.workspace.builder.protocol import WorkspaceBuilderProtocol

WORKSPACE_BUILDERS_GROUP = "tmuxp.workspace_builders"
"""Entry-point group packaged builders register under."""


def resolve_builder_paths(
    session_config: dict[str, t.Any],
    workspace_file: str | os.PathLike[str] | None = None,
) -> list[pathlib.Path]:
    """Resolve and validate trusted ``workspace_builder_paths`` import roots.

    Each entry is shell-expanded (``~`` and ``$VARS``), resolved relative to the
    workspace file's directory when not absolute, and required to be an existing
    directory. Returns ``[]`` when the key is absent, so existing workspaces add
    nothing to ``sys.path``.

    Parameters
    ----------
    session_config : dict
        the expanded workspace configuration
    workspace_file : str or os.PathLike, optional
        path to the workspace file; its parent anchors relative entries

    Returns
    -------
    list of pathlib.Path

    Examples
    --------
    Absent key resolves to an empty list (no-op for existing workspaces):

    >>> resolve_builder_paths({}, None)
    []

    An existing directory is resolved:

    >>> root = tmp_path / "roots"
    >>> root.mkdir()
    >>> resolve_builder_paths({"workspace_builder_paths": [str(root)]}, None) == [
    ...     root.resolve()
    ... ]
    True

    A missing directory is rejected:

    >>> resolve_builder_paths(
    ...     {"workspace_builder_paths": [str(tmp_path / "missing")]}, None
    ... )
    Traceback (most recent call last):
    ...
    tmuxp.exc.WorkspaceBuilderPathError: ...
    """
    raw = session_config.get("workspace_builder_paths") or []
    if isinstance(raw, (str, os.PathLike)):
        raw = [raw]

    base = (
        pathlib.Path(workspace_file).parent
        if workspace_file is not None
        else pathlib.Path.cwd()
    )

    resolved: list[pathlib.Path] = []
    for entry in raw:
        if not isinstance(entry, (str, os.PathLike)):
            raise exc.WorkspaceBuilderPathError(
                str(entry),
                reason="entries must be path strings",
            )
        candidate = pathlib.Path(expandshell(str(entry)))
        if not candidate.is_absolute():
            candidate = base / candidate
        candidate = candidate.resolve()
        if not candidate.is_dir():
            raise exc.WorkspaceBuilderPathError(str(PrivatePath(candidate)))
        resolved.append(candidate)
    return resolved


@contextlib.contextmanager
def prepended_sys_path(
    paths: list[pathlib.Path] | None,
) -> Iterator[None]:
    """Temporarily prepend directories to ``sys.path``, restoring it on exit.

    Paths are prepended in order (first entry ends up at ``sys.path[0]``). An
    empty or falsy ``paths`` is a no-op. Uses only literal directory entries; it
    avoids :func:`site.addsitedir` (which runs ``.pth`` startup code).

    Parameters
    ----------
    paths : list of pathlib.Path or None
        directories to prepend

    Examples
    --------
    >>> import sys
    >>> ext = tmp_path / "ext"
    >>> ext.mkdir()
    >>> before = list(sys.path)
    >>> with prepended_sys_path([ext]):
    ...     sys.path[0] == str(ext)
    True
    >>> sys.path == before
    True
    """
    if not paths:
        yield
        return
    saved = list(sys.path)
    for path in reversed(paths):
        sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path[:] = saved


def available_builders() -> list[str]:
    """Return the names of builders registered via entry points.

    Examples
    --------
    >>> isinstance(available_builders(), list)
    True
    """
    return [ep.name for ep in metadata.entry_points(group=WORKSPACE_BUILDERS_GROUP)]


def _load_entry_point(name: str) -> t.Any | None:
    """Load a builder registered under entry-point ``name``, else ``None``.

    Examples
    --------
    >>> _load_entry_point("definitely-not-a-registered-builder") is None
    True
    """
    for ep in metadata.entry_points(group=WORKSPACE_BUILDERS_GROUP):
        if ep.name == name:
            try:
                return ep.load()
            except (ImportError, AttributeError) as e:
                raise exc.WorkspaceBuilderImportError(name, reason=str(e)) from e
    return None


def _import_target(target: str) -> t.Any:
    """Import an object from a ``module:attr`` or dotted ``module.attr`` path.

    Examples
    --------
    >>> _import_target(
    ...     "tmuxp.workspace.builder.classic:ClassicWorkspaceBuilder"
    ... ).__name__
    'ClassicWorkspaceBuilder'

    The historical ``tmuxp.workspace.builder:WorkspaceBuilder`` alias resolves
    to the same class:

    >>> _import_target("tmuxp.workspace.builder:WorkspaceBuilder").__name__
    'ClassicWorkspaceBuilder'
    """
    if ":" in target:
        module_name, _, attr = target.partition(":")
    else:
        module_name, _, attr = target.rpartition(".")
    if not module_name or not attr:
        raise exc.WorkspaceBuilderNotFound(target)
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        raise exc.WorkspaceBuilderImportError(target, reason=str(e)) from e
    obj: t.Any = module
    try:
        for part in attr.split("."):
            obj = getattr(obj, part)
    except AttributeError as e:
        raise exc.WorkspaceBuilderImportError(target, reason=str(e)) from e
    return obj


def _validate_builder(obj: t.Any, target: str) -> None:
    """Validate that ``obj`` is a usable workspace builder.

    A class must expose a callable ``build`` method and a constructor accepting
    ``session_config`` and ``server`` (or ``**kwargs``). Non-class callables
    (factories) are trusted and validated at instantiation.

    Examples
    --------
    >>> from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder
    >>> _validate_builder(ClassicWorkspaceBuilder, "classic")

    >>> _validate_builder(object, "object")
    Traceback (most recent call last):
    ...
    tmuxp.exc.InvalidWorkspaceBuilder: 'object' is not a valid workspace builder: ...
    """
    if inspect.isclass(obj):
        if not callable(getattr(obj, "build", None)):
            raise exc.InvalidWorkspaceBuilder(
                target,
                reason="class has no callable 'build' method",
            )
        try:
            params = inspect.signature(obj).parameters
        except (TypeError, ValueError):
            return
        has_var_kw = any(
            p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()
        )
        missing = {"session_config", "server"} - set(params)
        if not has_var_kw and missing:
            joined = ", ".join(sorted(missing))
            raise exc.InvalidWorkspaceBuilder(
                target,
                reason=f"constructor missing parameter(s): {joined}",
            )
    elif not callable(obj):
        raise exc.InvalidWorkspaceBuilder(target, reason="not a class or callable")


def resolve_builder_class(
    session_config: dict[str, t.Any],
) -> type[WorkspaceBuilderProtocol]:
    """Resolve the workspace builder class selected by ``session_config``.

    Resolution of the ``workspace_builder`` value:

    1. absent/empty → the classic
       :class:`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder` (no
       import, no entry-point scan);
    2. contains ``:`` → a ``module:attr`` object reference;
    3. no ``.`` and no ``:`` → an entry-point name in the
       ``tmuxp.workspace_builders`` group;
    4. dotted, no ``:`` → an entry-point name if registered, otherwise a
       ``module.attr`` dotted path.

    Parameters
    ----------
    session_config : dict
        the expanded workspace configuration

    Returns
    -------
    type
        a workspace builder class (or builder factory) satisfying
        :class:`~tmuxp.workspace.builder.protocol.WorkspaceBuilderProtocol`

    Examples
    --------
    The default resolves to the classic builder without importing anything:

    >>> from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder
    >>> resolve_builder_class({}) is ClassicWorkspaceBuilder
    True

    A dotted ``module:attr`` reference is imported and validated:

    >>> resolve_builder_class(
    ...     {
    ...         "workspace_builder": (
    ...             "tmuxp.workspace.builder.classic:ClassicWorkspaceBuilder"
    ...         )
    ...     }
    ... ) is ClassicWorkspaceBuilder
    True
    """
    target = session_config.get("workspace_builder")
    if not target:
        return ClassicWorkspaceBuilder
    target_str = str(target).strip()

    obj: t.Any
    if ":" in target_str:
        obj = _import_target(target_str)
    elif "." not in target_str:
        obj = _load_entry_point(target_str)
        if obj is None:
            raise exc.WorkspaceBuilderNotFound(
                target_str,
                available=available_builders(),
            )
    else:
        obj = _load_entry_point(target_str)
        if obj is None:
            obj = _import_target(target_str)

    _validate_builder(obj, target_str)
    return t.cast("type[WorkspaceBuilderProtocol]", obj)
