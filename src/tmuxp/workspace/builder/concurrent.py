"""Concurrent workspace builder.

:class:`ConcurrentWorkspaceBuilder` is an opt-in builder that speeds up loads by
observing pane readiness *concurrently* within a window. Where the classic
builder creates each pane, waits for its prompt, lays out, and dispatches its
commands one pane at a time, this builder creates all of a window's panes up
front so their shells warm up together, waits for them in a single shared
barrier, lays the window out once, then dispatches each pane's commands.

Select it from a workspace file with ``workspace_builder: concurrent`` (it is
registered under the ``tmuxp.workspace_builders`` entry-point group). It honors
the same ``workspace_builder_options.pane_readiness`` policy as the classic
builder and falls back to the classic one-pane-at-a-time path for windows whose
later panes depend on an earlier pane's ``start_directory`` side effects.
"""

from __future__ import annotations

import logging
import os
import pathlib
import time
import typing as t

from libtmux.exc import LibTmuxException
from libtmux.pane import Pane
from libtmux.window import Window

from tmuxp.log import TmuxpLoggerAdapter
from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder

if t.TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


def _pane_has_drawn_prompt(pane: Pane) -> bool:
    """Return whether a pane's shell has drawn its prompt.

    The cursor leaving the origin ``(0, 0)`` is the signal that the shell has
    finished initializing and rendered its first prompt. Resizing a pane before
    this point races zsh's prompt redraw and surfaces its partial-line ``%``
    marker (issue #365), so the build waits for this to become true before
    applying layouts or sending keys.

    Parameters
    ----------
    pane : :class:`libtmux.Pane`
        pane whose freshly refreshed cursor position to inspect

    Returns
    -------
    bool
        True once the cursor has moved away from ``(0, 0)``

    Examples
    --------
    >>> pane = session.active_window.active_pane
    >>> _ = _wait_for_panes_ready([pane], timeout=5.0)
    >>> _pane_has_drawn_prompt(pane)
    True
    """
    return pane.cursor_x != "0" or pane.cursor_y != "0"


def _wait_for_panes_ready(
    panes: list[Pane],
    timeout: float = 2.0,
    interval: float = 0.01,
) -> dict[str, bool]:
    """Wait for many panes to draw their prompts, sharing one timeout budget.

    tmux spawns each pane's shell the moment the pane is created, so the shells
    initialize concurrently. Polling every pane in a single loop — rather than
    blocking on each one to completion before starting the next — observes that
    concurrency, collapsing the worst case from ``len(panes) * timeout`` of
    serial waiting into a single shared ``timeout`` window. A slow prompt that
    exceeds the timeout continues without blocking the rest of the workspace.

    Parameters
    ----------
    panes : list of :class:`libtmux.Pane`
        panes to wait for; panes without an id are ignored
    timeout : float
        maximum seconds to wait for the whole set before giving up
    interval : float
        seconds between polling sweeps

    Returns
    -------
    dict of str to bool
        maps each pane id to whether it became ready before the timeout

    Examples
    --------
    >>> pane = session.active_window.active_pane
    >>> _wait_for_panes_ready([pane], timeout=5.0)
    {'%...': True}
    """
    pending = {p.pane_id: p for p in panes if p.pane_id is not None}
    ready: dict[str, bool] = {}
    start = time.monotonic()
    while pending and time.monotonic() - start < timeout:
        for pane_id, pane in list(pending.items()):
            try:
                pane.refresh()
            except Exception:
                logger.debug(
                    "pane refresh failed during readiness check",
                    exc_info=True,
                    extra={"tmux_pane": str(pane_id)},
                )
                ready[pane_id] = False
                del pending[pane_id]
                continue
            if _pane_has_drawn_prompt(pane):
                logger.debug(
                    "pane ready, cursor moved from origin",
                    extra={"tmux_pane": str(pane_id)},
                )
                ready[pane_id] = True
                del pending[pane_id]
        if pending:
            time.sleep(interval)
    for pane_id in pending:
        logger.debug(
            "pane readiness check timed out after %.1f seconds",
            timeout,
            extra={"tmux_pane": str(pane_id)},
        )
        ready[pane_id] = False
    return ready


def _pane_start_directory(
    pane_config: dict[str, t.Any],
    window_config: dict[str, t.Any],
) -> str | None:
    """Resolve a pane's split-time ``start_directory``.

    A pane-level value wins over a window-level one; ``None`` when neither is
    set.

    Examples
    --------
    >>> _pane_start_directory({"start_directory": "/tmp"}, {})
    '/tmp'
    >>> _pane_start_directory({}, {"start_directory": "/var"})
    '/var'
    >>> _pane_start_directory({}, {}) is None
    True
    """
    if "start_directory" in pane_config:
        return t.cast("str", pane_config["start_directory"])
    if "start_directory" in window_config:
        return t.cast("str", window_config["start_directory"])
    return None


def _pane_shell(
    pane_config: dict[str, t.Any],
    window_config: dict[str, t.Any],
) -> str | None:
    """Resolve a pane's split-time shell launcher.

    A pane-level ``shell`` wins over a window-level ``window_shell``; ``None``
    when neither is set (the pane runs the default interactive shell).

    Examples
    --------
    >>> _pane_shell({"shell": "top"}, {})
    'top'
    >>> _pane_shell({}, {"window_shell": "htop"})
    'htop'
    >>> _pane_shell({}, {}) is None
    True
    """
    if "shell" in pane_config:
        return t.cast("str", pane_config["shell"])
    if "window_shell" in window_config:
        return t.cast("str", window_config["window_shell"])
    return None


class _PaneEntry(t.NamedTuple):
    """A created pane awaiting the readiness barrier, layout, and its commands.

    Carries the bits the later build phases need once every shell is ready: the
    pane, its config section, and the resolved custom ``shell`` (``None`` for a
    default-shell pane, which is the only kind whose prompt the build waits on).
    """

    pane: Pane
    config: dict[str, t.Any]
    shell: str | None


class ConcurrentWorkspaceBuilder(ClassicWorkspaceBuilder):
    """Build a workspace, observing each window's pane readiness concurrently.

    A drop-in for :class:`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder`
    that overrides the per-window construction seam
    (:meth:`~tmuxp.workspace.builder.classic.ClassicWorkspaceBuilder._build_window`)
    with a three-phase strategy: create all of a window's panes, wait for their
    shells in one shared barrier, lay out once, then dispatch each pane's
    commands. Session creation, window iteration, options, focus, plugin hooks,
    ``before_script``, and the ``on_build_event`` milestones are inherited from
    the classic builder unchanged.

    Examples
    --------
    >>> import yaml
    >>> session_config = yaml.load('''
    ...     session_name: concurrent sample
    ...     windows:
    ...     - window_name: editor
    ...       layout: main-vertical
    ...       panes:
    ...       - shell_command:
    ...         - cmd: echo "one"
    ...       - shell_command:
    ...         - cmd: echo "two"
    ... ''', Loader=yaml.Loader)
    >>> builder = ConcurrentWorkspaceBuilder(
    ...     session_config=session_config, server=server,
    ... )
    >>> builder.build()
    >>> builder.session.name
    'concurrent sample'
    >>> len(builder.session.windows[0].panes)
    2
    """

    def _build_window(
        self,
        window: Window,
        window_config: dict[str, t.Any],
    ) -> Pane | None:
        """Build a window's panes concurrently; return its focus pane.

        Overrides the classic per-window seam with a three-phase strategy:

        1. create every pane up front so their shells warm up together;
        2. wait once for the default-shell panes to draw their prompts (only
           when the resolved ``pane_readiness`` policy says to wait);
        3. lay the window out a single time, then send each pane its commands.

        A window whose later panes depend on an earlier pane's
        ``start_directory`` side effects falls back to the classic
        one-pane-at-a-time path.

        Parameters
        ----------
        window : :class:`libtmux.Window`
            the window to populate
        window_config : dict
            config section for the window

        Returns
        -------
        :class:`libtmux.Pane` or None
            the pane that requested focus, or ``None`` when no pane did

        Examples
        --------
        >>> session = server.new_session("concurrent-build-window")
        >>> builder = ConcurrentWorkspaceBuilder(
        ...     session_config={"session_name": "x", "windows": []},
        ...     server=server,
        ... )
        >>> window_config = {
        ...     "window_name": "main",
        ...     "layout": "tiled",
        ...     "panes": [{"shell_command": []}, {"shell_command": []}],
        ... }
        >>> builder._build_window(session.active_window, window_config) is None
        True
        >>> len(session.active_window.panes)
        2
        """
        if self._window_needs_sequential_pane_setup(window_config):
            pane_iter = self._iter_create_panes_sequentially(window, window_config)
        else:
            entries = self._create_window_panes(window, window_config)
            if self._pane_readiness_wait:
                self._wait_for_window_panes_ready(entries)
            pane_iter = self._dispatch_window_commands(window, window_config, entries)

        focus_pane: Pane | None = None
        for pane, pane_config in pane_iter:
            assert isinstance(pane, Pane)
            if pane_config.get("focus"):
                focus_pane = pane
        return focus_pane

    def _window_needs_sequential_pane_setup(
        self,
        window_config: dict[str, t.Any],
    ) -> bool:
        """Return whether later pane splits depend on missing directories.

        When a later pane's ``start_directory`` does not yet exist, an earlier
        pane's command may be expected to create it before the split runs. Such
        a window cannot create its panes up front, so it falls back to the
        classic sequential path.

        Examples
        --------
        >>> builder = ConcurrentWorkspaceBuilder(
        ...     session_config={'session_name': 'x', 'windows': []},
        ...     server=server,
        ... )
        >>> builder._window_needs_sequential_pane_setup({
        ...     'panes': [
        ...         {'shell_command': []},
        ...         {'shell_command': [], 'start_directory': '/'},
        ...     ],
        ... })
        False
        >>> builder._window_needs_sequential_pane_setup({
        ...     'panes': [
        ...         {'shell_command': []},
        ...         {
        ...             'shell_command': [],
        ...             'start_directory': '/__tmuxp_missing_start_directory__',
        ...         },
        ...     ],
        ... })
        True
        """
        for pane_config in window_config["panes"][1:]:
            start_directory = pane_config.get(
                "start_directory",
                window_config.get("start_directory"),
            )
            if (
                start_directory is not None
                and not pathlib.Path(os.fspath(start_directory)).expanduser().is_dir()
            ):
                return True
        return False

    def _create_pane(
        self,
        window: Window,
        window_config: dict[str, t.Any],
        pane_config: dict[str, t.Any],
        prev_pane: Pane | None,
        layout: str | None,
        entries: list[_PaneEntry],
    ) -> Pane:
        """Create the active or a freshly split pane for ``pane_config``.

        ``prev_pane`` is ``None`` for the window's first pane (which reuses the
        window's active pane); otherwise the pane is split off ``prev_pane``,
        reclaiming space on demand.

        Parameters
        ----------
        window : :class:`libtmux.Window`
            window the pane belongs to
        window_config : dict
            config section for the window
        pane_config : dict
            config section for the pane
        prev_pane : :class:`libtmux.Pane` or None
            pane to split from, or ``None`` for the first pane
        layout : str or None
            window layout used to reclaim space, if configured
        entries : list of :class:`_PaneEntry`
            panes created so far, waited on before reclaiming space

        Returns
        -------
        :class:`libtmux.Pane`
            the created or reused pane

        Examples
        --------
        >>> session = server.new_session("concurrent-create-pane")
        >>> builder = ConcurrentWorkspaceBuilder(
        ...     session_config={"session_name": "x", "windows": []},
        ...     server=server,
        ... )
        >>> window_config = {"window_name": "main", "panes": [{"shell_command": []}]}
        >>> pane = builder._create_pane(
        ...     session.active_window, window_config,
        ...     window_config["panes"][0], None, None, [],
        ... )
        >>> pane is not None
        True
        """
        if prev_pane is None:
            pane = window.active_pane
        else:
            split_kwargs: dict[str, t.Any] = {
                "attach": True,
                "start_directory": _pane_start_directory(pane_config, window_config),
                "shell": _pane_shell(pane_config, window_config),
                "environment": pane_config.get(
                    "environment",
                    window_config.get("environment"),
                ),
            }
            pane = self._split_pane_reclaiming_space(
                window,
                prev_pane,
                split_kwargs,
                layout,
                entries,
            )

        assert isinstance(pane, Pane)
        TmuxpLoggerAdapter(
            logger,
            {
                "tmux_session": window.session.name or "",
                "tmux_window": window.name or "",
                "tmux_pane": pane.pane_id or "",
            },
        ).debug("pane created")
        return pane

    def _create_window_panes(
        self,
        window: Window,
        window_config: dict[str, t.Any],
    ) -> list[_PaneEntry]:
        """Create a window's panes without waiting, laying out, or sending keys.

        The first build phase. Splitting the panes back-to-back lets their
        shells initialize concurrently while the build moves on; readiness,
        layout, and commands are deferred to later phases. Each split resizes the
        pane it targets, and the build only ever splits the newest pane — one
        created microseconds earlier, still sourcing its rc and therefore safe to
        resize. The exception is running out of room, handled by
        :meth:`_split_pane_reclaiming_space`.

        Parameters
        ----------
        window : :class:`libtmux.Window`
            window to create panes for
        window_config : dict
            config section for the window

        Returns
        -------
        list of :class:`_PaneEntry`
            one entry per created pane, in config order

        Examples
        --------
        >>> session = server.new_session("concurrent-create-window-panes")
        >>> builder = ConcurrentWorkspaceBuilder(
        ...     session_config={"session_name": "x", "windows": []},
        ...     server=server,
        ... )
        >>> entries = builder._create_window_panes(
        ...     session.active_window,
        ...     {"window_name": "main", "panes": [{"shell_command": []},
        ...      {"shell_command": []}]},
        ... )
        >>> len(entries)
        2
        >>> entries[0].shell is None
        True
        """
        assert isinstance(window, Window)

        pane_base_index = window.show_option("pane-base-index", global_=True)
        assert pane_base_index is not None

        layout = window_config.get("layout")
        entries: list[_PaneEntry] = []
        prev_pane: Pane | None = None
        panes = window_config["panes"]
        total = len(panes)

        for offset, pane_config in enumerate(panes):
            if self.on_progress:
                self.on_progress(f"Creating pane: {int(pane_base_index) + offset}")
            if self.on_build_event:
                self.on_build_event(
                    {
                        "event": "pane_creating",
                        "pane_num": offset + 1,
                        "pane_total": total,
                    },
                )

            pane = self._create_pane(
                window,
                window_config,
                pane_config,
                prev_pane,
                layout,
                entries,
            )
            pane_shell = pane_config.get("shell", window_config.get("window_shell"))
            entries.append(_PaneEntry(pane=pane, config=pane_config, shell=pane_shell))
            prev_pane = pane

        return entries

    def _iter_create_panes_sequentially(
        self,
        window: Window,
        window_config: dict[str, t.Any],
    ) -> Iterator[t.Any]:
        """Create, wait, and dispatch a window's panes one at a time.

        The compatibility path that preserves configs where an earlier pane's
        command prepares a later pane's split-time ``start_directory``.

        Parameters
        ----------
        window : :class:`libtmux.Window`
            window to create panes for
        window_config : dict
            config section for the window

        Yields
        ------
        tuple of (:class:`libtmux.Pane`, ``pane_config``)
            each pane and the config section used to create it

        Examples
        --------
        >>> session = server.new_session("concurrent-create-sequentially")
        >>> builder = ConcurrentWorkspaceBuilder(
        ...     session_config={"session_name": "x", "windows": []},
        ...     server=server,
        ... )
        >>> panes = list(
        ...     builder._iter_create_panes_sequentially(
        ...         session.active_window,
        ...         {"window_name": "main", "panes": [{"shell_command": []}]},
        ...     ),
        ... )
        >>> len(panes)
        1
        """
        assert isinstance(window, Window)

        pane_base_index = window.show_option("pane-base-index", global_=True)
        assert pane_base_index is not None

        layout = window_config.get("layout")
        entries: list[_PaneEntry] = []
        prev_pane: Pane | None = None
        panes = window_config["panes"]
        total = len(panes)

        for offset, pane_config in enumerate(panes):
            if self.on_progress:
                self.on_progress(f"Creating pane: {int(pane_base_index) + offset}")
            if self.on_build_event:
                self.on_build_event(
                    {
                        "event": "pane_creating",
                        "pane_num": offset + 1,
                        "pane_total": total,
                    },
                )

            pane = self._create_pane(
                window,
                window_config,
                pane_config,
                prev_pane,
                layout,
                entries,
            )
            pane_shell = pane_config.get("shell", window_config.get("window_shell"))
            entry = _PaneEntry(pane=pane, config=pane_config, shell=pane_shell)
            entries.append(entry)
            prev_pane = pane

            if self._pane_readiness_wait:
                self._wait_for_window_panes_ready([entry])
            yield from self._dispatch_window_commands(window, window_config, [entry])

    def _split_pane_reclaiming_space(
        self,
        window: Window,
        pane: Pane,
        split_kwargs: dict[str, t.Any],
        layout: str | None,
        entries: list[_PaneEntry],
    ) -> Pane:
        """Split ``pane``; if it fails for space and a layout is set, retry.

        Without an intermediate ``select_layout`` after every split, a window
        with many panes eventually has no room for the next split. Reclaiming
        space resizes created panes, so default-shell panes are waited on first.
        With no layout to redistribute with, the split failure propagates (the
        genuine #800 "no space" error for a window that is simply too small).

        Parameters
        ----------
        window : :class:`libtmux.Window`
            window the panes belong to
        pane : :class:`libtmux.Pane`
            pane to split
        split_kwargs : dict
            keyword arguments forwarded to :meth:`libtmux.Pane.split`
        layout : str or None
            window layout used to reclaim space, if configured
        entries : list of :class:`_PaneEntry`
            panes created so far, waited on before reclaiming space

        Returns
        -------
        :class:`libtmux.Pane`
            the newly split pane

        Examples
        --------
        >>> session = server.new_session("concurrent-reclaim-space")
        >>> builder = ConcurrentWorkspaceBuilder(
        ...     session_config={"session_name": "x", "windows": []},
        ...     server=server,
        ... )
        >>> first = session.active_window.active_pane
        >>> second = builder._split_pane_reclaiming_space(
        ...     session.active_window, first, {"attach": True}, "tiled", [],
        ... )
        >>> second is not None
        True
        """
        # libtmux resolves ``pane.window`` during split; refresh keeps the
        # target pane's window id current without waiting for a shell prompt.
        pane.refresh()
        try:
            return pane.split(**split_kwargs)
        except LibTmuxException as error:
            if layout is None or "no space for" not in str(error):
                raise
            _wait_for_panes_ready([e.pane for e in entries if e.shell is None])
            window.select_layout(layout)
            return pane.split(**split_kwargs)

    def _wait_for_window_panes_ready(
        self,
        entries: list[_PaneEntry],
    ) -> dict[str, bool]:
        """Wait for a window's default-shell panes in one shared barrier.

        Collects the panes that draw an interactive prompt (those without a
        custom ``shell`` launcher) and waits for them together through
        :func:`_wait_for_panes_ready`.

        Parameters
        ----------
        entries : list of :class:`_PaneEntry`
            created panes for the window

        Returns
        -------
        dict of str to bool
            maps each waited pane id to whether it became ready

        Examples
        --------
        >>> session = server.new_session("concurrent-window-ready")
        >>> builder = ConcurrentWorkspaceBuilder(
        ...     session_config={"session_name": "x", "windows": []},
        ...     server=server,
        ... )
        >>> window_config = {"window_name": "main", "panes": [{"shell_command": []}]}
        >>> entries = builder._create_window_panes(
        ...     session.active_window, window_config,
        ... )
        >>> sorted(builder._wait_for_window_panes_ready(entries).values())
        [True]
        """
        panes = [entry.pane for entry in entries if entry.shell is None]
        return _wait_for_panes_ready(panes)

    def _dispatch_window_commands(
        self,
        window: Window,
        window_config: dict[str, t.Any],
        entries: list[_PaneEntry],
    ) -> Iterator[t.Any]:
        """Lay the window out, then send each pane its ``shell_command``.

        The final build phase, run after the readiness barrier. Applying the
        layout here is a single resize with every default-shell pane already past
        its prompt, which keeps zsh from printing its partial-line ``%`` marker
        (issue #365).

        Parameters
        ----------
        window : :class:`libtmux.Window`
            window to finish
        window_config : dict
            config section for the window
        entries : list of :class:`_PaneEntry`
            panes created for this window

        Yields
        ------
        tuple of (:class:`libtmux.Pane`, ``pane_config``)
            each pane and the config section used to create it

        Examples
        --------
        >>> session = server.new_session("concurrent-dispatch-window")
        >>> builder = ConcurrentWorkspaceBuilder(
        ...     session_config={"session_name": "x", "windows": []},
        ...     server=server,
        ... )
        >>> window_config = {
        ...     "window_name": "main", "layout": "tiled",
        ...     "panes": [{"shell_command": []}],
        ... }
        >>> entries = builder._create_window_panes(
        ...     session.active_window, window_config,
        ... )
        >>> _ = builder._wait_for_window_panes_ready(entries)
        >>> dispatched = list(
        ...     builder._dispatch_window_commands(
        ...         session.active_window, window_config, entries,
        ...     ),
        ... )
        >>> len(dispatched)
        1
        """
        if "layout" in window_config:
            window.select_layout(window_config["layout"])

        for pane, pane_config, _pane_shell in entries:
            pane_log = TmuxpLoggerAdapter(
                logger,
                {
                    "tmux_session": window.session.name or "",
                    "tmux_window": window.name or "",
                    "tmux_pane": pane.pane_id or "",
                },
            )

            if "suppress_history" in pane_config:
                suppress = pane_config["suppress_history"]
            elif "suppress_history" in window_config:
                suppress = window_config["suppress_history"]
            else:
                suppress = True

            enter = pane_config.get("enter", True)
            sleep_before = pane_config.get("sleep_before", None)
            sleep_after = pane_config.get("sleep_after", None)
            for cmd in pane_config["shell_command"]:
                enter = cmd.get("enter", enter)
                sleep_before = cmd.get("sleep_before", sleep_before)
                sleep_after = cmd.get("sleep_after", sleep_after)

                if sleep_before is not None:
                    time.sleep(sleep_before)

                pane.send_keys(cmd["cmd"], suppress_history=suppress, enter=enter)
                pane_log.debug("sent command %s", cmd["cmd"])

                if sleep_after is not None:
                    time.sleep(sleep_after)

            if pane_config.get("focus"):
                assert pane.pane_id is not None
                window.select_pane(pane.pane_id)

            yield pane, pane_config
