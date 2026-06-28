"""Public contract for tmuxp workspace builders.

A workspace builder turns an expanded workspace ``dict`` into a live tmux
session. :class:`tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder` is the
default implementation; third parties may ship their own and select them with
the ``workspace_builder`` config key (see
:mod:`tmuxp.workspace.builder.registry`).

This module is intentionally dependency-light (typing only) so builder authors
can import the contract without pulling in tmuxp's resolution machinery.

The contract is synchronous today. Async builders are an *additive* future
extension: a subclass protocol can declare an ``async`` build entry point and a
capability flag, discovered through the same entry-point group, without
changing this sync surface.
"""

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from libtmux.server import Server
    from libtmux.session import Session


@t.runtime_checkable
class WorkspaceBuilderProtocol(t.Protocol):
    """Contract a builder must satisfy to be driven by ``tmuxp load``.

    A conforming builder is constructed with at least ``session_config`` and
    ``server`` (plus the optional ``plugins`` and ``on_*`` callbacks the classic
    builder accepts). It exposes :meth:`build`, surfaces the populated tmux
    session via :attr:`session`, and honors the plugin/progress integration
    points the CLI drives.

    Because the protocol carries data members (``session``, ``plugins``, the
    ``on_*`` callbacks), validate *instances* with :func:`isinstance`;
    class-level ``issubclass`` checks are not supported for runtime-checkable
    protocols with non-method members.

    Examples
    --------
    A builder implementing the full contract satisfies the protocol:

    >>> from tmuxp.workspace.builder.protocol import WorkspaceBuilderProtocol
    >>> class MiniBuilder:
    ...     plugins: list = []
    ...     on_progress = None
    ...     on_before_script = None
    ...     on_script_output = None
    ...     on_build_event = None
    ...     def __init__(self, session_config, server, **kwargs):
    ...         self._session_config = session_config
    ...     def build(self, session=None, append=False):
    ...         ...
    ...     def session_exists(self, session_name):
    ...         ...
    ...     def find_current_attached_session(self):
    ...         ...
    ...     @property
    ...     def session(self):
    ...         ...
    >>> builder = MiniBuilder(session_config={}, server=None)
    >>> isinstance(builder, WorkspaceBuilderProtocol)
    True

    An object missing the contract does not:

    >>> isinstance(object(), WorkspaceBuilderProtocol)
    False
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
        """Construct a builder from an expanded workspace and a tmux server."""
        ...

    @property
    def session(self) -> Session:
        """Return the tmux session the builder created or populated."""
        ...

    def build(self, session: Session | None = None, append: bool = False) -> None:
        """Build the workspace, creating or populating a tmux session."""
        ...

    def session_exists(self, session_name: str) -> bool:
        """Return ``True`` if a session with ``session_name`` already exists."""
        ...

    def find_current_attached_session(self) -> Session:
        """Return the session currently attached within ``$TMUX``."""
        ...
