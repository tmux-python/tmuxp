"""An async, folding workspace builder backed by libtmux's engine-ops.

:class:`EngineOpsWorkspaceBuilder` is an opt-in
:class:`~tmuxp.workspace.builder.protocol.WorkspaceBuilderProtocol` that lowers an
expanded workspace ``dict`` to libtmux's declarative
:class:`~libtmux.experimental.workspace.ir.Workspace` and ``abuild``s it
asynchronously. The build *folds*: a multi-pane window's commands collapse into a
handful of ``;``-chained tmux dispatches instead of one ``send-keys`` per line,
so a session renders in a few round-trips rather than dozens.

Select it with the ``workspace_builder: engine-ops`` config key or ``tmuxp load
--engine-ops``.

The engine-ops workspace API is unreleased (``libtmux.experimental``); this
module is usable only with the branch pin in ``pyproject.toml``.
"""

from __future__ import annotations

import asyncio
import typing as t

from libtmux._internal.query_list import ObjectDoesNotExist
from libtmux.experimental.engines import AsyncSubprocessEngine
from libtmux.experimental.workspace import analyze
from libtmux.experimental.workspace.events import (
    PaneCreated,
    SessionCreated,
    WindowCreated,
    WorkspaceBuilt,
)
from libtmux.server import Server

from tmuxp import exc
from tmuxp.util import get_current_pane

if t.TYPE_CHECKING:
    from libtmux.experimental.workspace.events import BuildEvent
    from libtmux.session import Session

#: Map an engine-ops structural event to the classic ``on_build_event`` name, so
#: a CLI progress UI written against the classic builder keeps working.
_EVENT_NAMES: dict[type[BuildEvent], str] = {
    SessionCreated: "session_created",
    WindowCreated: "window_done",
    PaneCreated: "pane_created",
    WorkspaceBuilt: "workspace_built",
}


class EngineOpsWorkspaceBuilder:
    """Build a workspace by folding it into a few async tmux dispatches.

    A drop-in builder that lowers the expanded config to libtmux's
    :class:`~libtmux.experimental.workspace.ir.Workspace` IR and ``abuild``s it;
    the result matches the classic builder's session/windows/panes, only the
    dispatch count differs.

    Selecting it by config key resolves to this class (a live build needs a
    server; see ``tests/workspace/test_builder_engine_ops.py``):

    Examples
    --------
    >>> from tmuxp.workspace.builder.registry import resolve_builder_class
    >>> resolve_builder_class({"workspace_builder": "engine-ops"}) is (
    ...     EngineOpsWorkspaceBuilder
    ... )
    True
    """

    plugins: list[t.Any]
    on_progress: t.Callable[[str], None] | None
    on_before_script: t.Callable[[], None] | None
    on_script_output: t.Callable[[str], None] | None
    on_build_event: t.Callable[[dict[str, t.Any]], None] | None

    def __init__(
        self,
        session_config: dict[str, t.Any],
        server: Server,
        plugins: list[t.Any] | None = None,
        on_progress: t.Callable[[str], None] | None = None,
        on_before_script: t.Callable[[], None] | None = None,
        on_script_output: t.Callable[[str], None] | None = None,
        on_build_event: t.Callable[[dict[str, t.Any]], None] | None = None,
    ) -> None:
        """Construct from an expanded workspace and a tmux server."""
        if not session_config:
            raise exc.EmptyWorkspaceException
        assert isinstance(server, Server)
        self.session_config = session_config
        self.server = server
        self.plugins = plugins if plugins is not None else []
        self.on_progress = on_progress
        self.on_before_script = on_before_script
        self.on_script_output = on_script_output
        self.on_build_event = on_build_event
        self._session: Session | None = None
        if self.session_exists(session_config["session_name"]):
            try:
                self._session = server.sessions.get(
                    session_name=session_config["session_name"],
                )
            except ObjectDoesNotExist:
                self._session = None

    @property
    def session(self) -> Session:
        """Return the tmux session the builder created or populated."""
        if self._session is None:
            raise exc.SessionMissingWorkspaceException
        return self._session

    def session_exists(self, session_name: str) -> bool:
        """Return ``True`` if a session with ``session_name`` already exists."""
        assert isinstance(session_name, str)
        if not self.server.has_session(session_name):
            return False
        try:
            self.server.sessions.get(session_name=session_name)
        except ObjectDoesNotExist:
            return False
        return True

    def find_current_attached_session(self) -> Session:
        """Return the session currently attached within ``$TMUX``."""
        current_active_pane = get_current_pane(self.server)
        if current_active_pane is None:
            raise exc.ActiveSessionMissingWorkspaceException
        return next(
            s
            for s in self.server.sessions
            if s.session_id == current_active_pane.session_id
        )

    def build(self, session: Session | None = None, append: bool = False) -> None:
        """Build the workspace by folding it into a few async dispatches.

        Lowers the config to a :class:`~..ir.Workspace`, ``abuild``s it over an
        :class:`~libtmux.experimental.engines.AsyncSubprocessEngine` bound to the
        server, and populates :attr:`session`. ``append`` is not supported (the
        IR always emits ``new-session``); use the classic builder for it.
        """
        if append:
            msg = "engine-ops builder does not support append; use the classic builder"
            raise NotImplementedError(msg)
        workspace = analyze(self.session_config)
        engine = AsyncSubprocessEngine.for_server(self.server)
        windows = self.session_config.get("windows", [])

        async def _bridge(event: BuildEvent) -> None:
            name = _EVENT_NAMES.get(type(event))
            if name is None or self.on_build_event is None:
                return
            payload: dict[str, t.Any] = {"event": name}
            if isinstance(event, SessionCreated):
                # The CLI progress spinner reads these keys on session_created;
                # they come from the config since the folded build has no live
                # per-window boundary to count from.
                payload["name"] = workspace.name
                payload["window_total"] = len(windows)
                payload["session_pane_total"] = sum(
                    len(w.get("panes", [])) for w in windows
                )
            self.on_build_event(payload)

        asyncio.run(workspace.abuild(engine, on_event=_bridge))

        built = self.server.sessions.get(session_name=workspace.name)
        assert built is not None
        self._session = built
        if self.on_progress is not None:
            self.on_progress("Workspace built")
