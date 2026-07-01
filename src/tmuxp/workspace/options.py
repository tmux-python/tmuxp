"""Behavior options for tmuxp workspace builders.

The ``workspace_builder_options`` config catalog holds settings that tune how a
workspace builder runs, independent of *which* builder is selected. It is a
sibling to the tmux ``options`` / ``global_options`` / ``environment`` catalogs
and is the home for builder-behavior knobs (today: pane readiness; later:
parallel/async builder settings).

Example
-------
.. code-block:: yaml

   workspace_builder_options:
     pane_readiness: auto   # auto | always | never (+ truthy/falsy aliases)
"""

from __future__ import annotations

import dataclasses
import enum
import os
import typing as t

from tmuxp import exc

_AUTO_ALIASES = frozenset({"auto"})
_ALWAYS_ALIASES = frozenset({"always", "true", "on", "yes", "1"})
_NEVER_ALIASES = frozenset({"never", "false", "off", "no", "0"})


class PaneReadiness(enum.Enum):
    """Policy for whether the builder waits for a pane's shell prompt.

    tmuxp waits for each default-shell pane to draw its prompt before
    dispatching layout and commands, which avoids a zsh prompt-redraw artifact
    (see :func:`tmuxp.workspace.builder.classic._wait_for_pane_ready`). The wait
    is only needed for zsh, so the default
    :attr:`~tmuxp.workspace.options.PaneReadiness.AUTO` policy waits only when
    the session's interactive shell is zsh.
    """

    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"

    @classmethod
    def from_config(cls, value: t.Any) -> PaneReadiness:
        """Parse a ``pane_readiness`` config value into a policy.

        Accepts the canonical ``auto`` / ``always`` / ``never`` strings, plus
        the truthy/falsy aliases users expect from boolean-like config keys.

        Parameters
        ----------
        value : Any
            value from ``workspace_builder_options.pane_readiness``; ``None``
            (key absent) resolves to
            :attr:`~tmuxp.workspace.options.PaneReadiness.AUTO`

        Returns
        -------
        PaneReadiness

        Examples
        --------
        >>> PaneReadiness.from_config(None) is PaneReadiness.AUTO
        True
        >>> PaneReadiness.from_config("auto") is PaneReadiness.AUTO
        True
        >>> PaneReadiness.from_config(True) is PaneReadiness.ALWAYS
        True
        >>> PaneReadiness.from_config("on") is PaneReadiness.ALWAYS
        True
        >>> PaneReadiness.from_config(1) is PaneReadiness.ALWAYS
        True
        >>> PaneReadiness.from_config(False) is PaneReadiness.NEVER
        True
        >>> PaneReadiness.from_config("never") is PaneReadiness.NEVER
        True

        Unknown values raise an actionable error:

        >>> PaneReadiness.from_config("sometimes")
        Traceback (most recent call last):
        ...
        ValueError: invalid pane_readiness value: 'sometimes'; expected one of:
        auto, always/true/on/yes/1, never/false/off/no/0
        """
        if value is None:
            return cls.AUTO
        if isinstance(value, cls):
            return value
        if isinstance(value, bool):
            return cls.ALWAYS if value else cls.NEVER
        normalized = str(value).strip().lower()
        if normalized in _AUTO_ALIASES:
            return cls.AUTO
        if normalized in _ALWAYS_ALIASES:
            return cls.ALWAYS
        if normalized in _NEVER_ALIASES:
            return cls.NEVER
        msg = (
            f"invalid pane_readiness value: {value!r}; expected one of: "
            "auto, always/true/on/yes/1, never/false/off/no/0"
        )
        raise ValueError(msg)


@dataclasses.dataclass(frozen=True)
class WorkspaceBuilderOptions:
    """Parsed ``workspace_builder_options`` catalog.

    An absent ``workspace_builder_options`` catalog uses the defaults, whose
    :attr:`PaneReadiness.AUTO` policy waits for a pane's prompt only when the
    session shell is zsh: zsh workspaces build as before, while bash, sh, and
    other shells skip the wait. Set ``pane_readiness: always`` to restore the
    previous wait-everywhere behavior.
    """

    pane_readiness: PaneReadiness = PaneReadiness.AUTO
    """pane-prompt wait policy; defaults to :attr:`PaneReadiness.AUTO`"""

    @classmethod
    def from_config(cls, session_config: dict[str, t.Any]) -> WorkspaceBuilderOptions:
        """Build options from a full workspace ``session_config`` dict.

        Reads the optional ``workspace_builder_options`` catalog; an absent or
        empty catalog yields the defaults (see the class docstring for how the
        default :attr:`PaneReadiness.AUTO` policy affects non-zsh shells).

        Parameters
        ----------
        session_config : dict
            the expanded workspace configuration

        Returns
        -------
        WorkspaceBuilderOptions

        Examples
        --------
        >>> WorkspaceBuilderOptions.from_config({}).pane_readiness
        <PaneReadiness.AUTO: 'auto'>

        >>> cfg = {"workspace_builder_options": {"pane_readiness": "always"}}
        >>> WorkspaceBuilderOptions.from_config(cfg).pane_readiness
        <PaneReadiness.ALWAYS: 'always'>
        """
        catalog = session_config.get("workspace_builder_options") or {}
        if not isinstance(catalog, dict):
            msg = f"must be a mapping, got {type(catalog).__name__}"
            raise exc.InvalidWorkspaceBuilderOption(msg)
        try:
            pane_readiness = PaneReadiness.from_config(catalog.get("pane_readiness"))
        except ValueError as e:
            raise exc.InvalidWorkspaceBuilderOption(str(e)) from e
        return cls(pane_readiness=pane_readiness)


def shell_is_zsh(shell: str | None) -> bool:
    """Return ``True`` when ``shell`` names the zsh shell.

    Parameters
    ----------
    shell : str or None
        a shell path or name (e.g. ``/usr/bin/zsh``)

    Returns
    -------
    bool

    Examples
    --------
    >>> shell_is_zsh("/usr/bin/zsh")
    True
    >>> shell_is_zsh("/bin/bash")
    False
    >>> shell_is_zsh(None)
    False
    """
    return "zsh" in (shell or "")


def resolve_session_shell(
    session: t.Any,
    env: t.Mapping[str, str] | None = None,
) -> str:
    """Resolve the effective interactive shell for a tmux session.

    Prefers tmux's ``default-shell`` option (which reflects a workspace's
    ``options.default-shell`` once applied, otherwise tmux's global default),
    and falls back to the ``SHELL`` environment variable.

    Parameters
    ----------
    session : :class:`libtmux.Session`
        live session exposing ``show_option("default-shell")``
    env : Mapping, optional
        environment mapping for the ``SHELL`` fallback; defaults to
        :data:`os.environ`

    Returns
    -------
    str
        resolved shell path/name, or ``""`` when undeterminable

    Examples
    --------
    >>> class FakeSession:
    ...     def __init__(self, shell):
    ...         self._shell = shell
    ...     def show_option(self, name, **kwargs):
    ...         return self._shell

    The tmux ``default-shell`` wins when set:

    >>> resolve_session_shell(FakeSession("/usr/bin/zsh"), env={})
    '/usr/bin/zsh'

    The ``SHELL`` env var is the fallback:

    >>> resolve_session_shell(FakeSession(None), env={"SHELL": "/bin/bash"})
    '/bin/bash'
    """
    # include_inherited resolves a globally-set default-shell (e.g.
    # ``set -g default-shell`` in tmux.conf) that the session inherits rather
    # than overrides; without it tmux returns None and we'd fall back to $SHELL.
    default_shell = session.show_option("default-shell", include_inherited=True)
    environ = os.environ if env is None else env
    env_shell = environ.get("SHELL", "")
    return str(default_shell or env_shell or "")
