"""Configuration import adapters to load teamocil, tmuxinator, etc. in tmuxp."""

from __future__ import annotations

import logging
import shlex
import typing as t

logger = logging.getLogger(__name__)


_SHELL_METACHAR_TOKENS = ("|", "&&", "||", ">", "<", "$(", "`", ";")

_FALSY_YAML_STRINGS = frozenset({"false", "no", "off"})


def _is_falsy_yaml(value: t.Any) -> bool:
    """Treat False, None, and YAML-style falsy strings as falsy.

    PyYAML usually decodes ``false`` to Python ``False``, but if a user
    quotes the value (``with_env_var: "false"``), it arrives as a
    truthy non-empty string. Coerce manually so the importer respects
    intent rather than Python's bool semantics.
    """
    if value is False or value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in _FALSY_YAML_STRINGS
    return False


def _has_shell_metachars(value: t.Any) -> bool:
    """Return True if value contains shell metacharacters that need a real shell.

    tmuxp's `before_script` runs via `subprocess.Popen` after `shlex.split()` —
    no shell process. Pipes, redirects, command substitution, and `&&` chains
    don't work. This helper flags such values so the caller can warn the user.

    Strings, lists of strings, and dicts containing strings are scanned. Any
    other type returns False (nothing to scan).

    >>> _has_shell_metachars("plain command")
    False
    >>> _has_shell_metachars("echo a | grep b")
    True
    >>> _has_shell_metachars(["safe", "echo $(date)"])
    True
    >>> _has_shell_metachars(None)
    False
    """
    if isinstance(value, str):
        return any(token in value for token in _SHELL_METACHAR_TOKENS)
    if isinstance(value, list):
        return any(_has_shell_metachars(item) for item in value)
    return False


def _parse_tmuxinator_tmux_args(
    args_str: str,
    target: dict[str, t.Any],
    session_name: str | None,
) -> None:
    """Parse tmuxinator `cli_args`/`tmux_options` into individual tmux flags.

    Splits via `shlex` and walks tokens to extract `-f` (config), `-L`
    (socket name), and `-S` (socket path). Unknown flags are warned.
    Mutates ``target`` in place.
    """
    mapping = {"-f": "config", "-L": "socket_name", "-S": "socket_path"}
    tokens = shlex.split(args_str)
    i = 0
    while i < len(tokens):
        flag = tokens[i]
        if flag in mapping:
            if i + 1 < len(tokens):
                target[mapping[flag]] = tokens[i + 1]
                i += 2
            else:
                logger.warning(
                    "tmux flag requires a value but none was provided",
                    extra={"tmux_key": flag, "tmux_session": session_name},
                )
                i += 1
        else:
            logger.warning(
                "unrecognized tmux flag in cli_args/tmux_options",
                extra={"tmux_key": flag, "tmux_session": session_name},
            )
            i += 1


def import_tmuxinator(workspace_dict: dict[str, t.Any]) -> dict[str, t.Any]:
    """Return tmuxp workspace from a `tmuxinator`_ yaml workspace.

    .. _tmuxinator: https://github.com/aziz/tmuxinator

    Parameters
    ----------
    workspace_dict : dict
        python dict for tmuxp workspace.

    Returns
    -------
    dict
    """
    # Top-level shallow copy so .pop()s below don't mutate the caller's dict.
    # Nested window/pane dicts are still mutated in place by the per-window
    # loop; if you pass a dict whose nested values are shared elsewhere,
    # deepcopy upstream.
    workspace_dict = {**workspace_dict}
    logger.debug(
        "importing tmuxinator workspace",
        extra={
            "tmux_session": workspace_dict.get("project_name")
            or workspace_dict.get("name", ""),
        },
    )

    tmuxp_workspace: dict[str, t.Any] = {}

    if "project_name" in workspace_dict:
        tmuxp_workspace["session_name"] = workspace_dict.pop("project_name")
    elif "name" in workspace_dict:
        tmuxp_workspace["session_name"] = workspace_dict.pop("name")
    else:
        tmuxp_workspace["session_name"] = None

    if "project_root" in workspace_dict:
        tmuxp_workspace["start_directory"] = workspace_dict.pop("project_root")
    elif "root" in workspace_dict:
        tmuxp_workspace["start_directory"] = workspace_dict.pop("root")

    args_str = workspace_dict.get("cli_args") or workspace_dict.get("tmux_options")
    if args_str:
        _parse_tmuxinator_tmux_args(
            args_str,
            tmuxp_workspace,
            tmuxp_workspace.get("session_name"),
        )

    if "socket_name" in workspace_dict:
        tmuxp_workspace["socket_name"] = workspace_dict["socket_name"]

    if "socket_path" in workspace_dict:
        tmuxp_workspace["socket_path"] = workspace_dict["socket_path"]

    if workspace_dict.get("attach") is False:
        logger.warning(
            "attach: false has no tmuxp config equivalent; pass `-d` to "
            "`tmuxp load` instead",
            extra={
                "tmux_key": "attach",
                "tmux_session": tmuxp_workspace.get("session_name"),
            },
        )

    tmuxp_workspace["windows"] = []

    if "tabs" in workspace_dict:
        workspace_dict["windows"] = workspace_dict.pop("tabs")

    # `pre` runs once before the session is created (template.erb:18-19).
    # `on_project_first_start` is the equivalent in the modern hook system
    # (project.rb:165-168) — fall back to it when `pre` is not set.
    pre_source = workspace_dict.get("pre")
    if pre_source is None and "on_project_first_start" in workspace_dict:
        pre_source = workspace_dict["on_project_first_start"]
    if pre_source is not None:
        if _has_shell_metachars(pre_source):
            logger.warning(
                "pre contains shell constructs that will not work in "
                "before_script (runs without shell=True)",
                extra={
                    "tmux_key": "pre",
                    "tmux_session": tmuxp_workspace.get("session_name"),
                },
            )
        tmuxp_workspace["before_script"] = pre_source

    # tmuxinator computes pre_window from an OR-fallback chain
    # (project.rb:175-188): rbenv -> rvm -> pre_tab -> pre_window. First
    # non-nil wins. `rbenv` and `rvm` are wrapped as shell commands.
    pre_window_chain: list[str] = []
    if "rbenv" in workspace_dict:
        pre_window_chain.append(f"rbenv shell {workspace_dict['rbenv']}")
    elif "rvm" in workspace_dict:
        pre_window_chain.append(f"rvm use {workspace_dict['rvm']}")
    elif "pre_tab" in workspace_dict:
        pre_window_chain.append(workspace_dict["pre_tab"])
    elif "pre_window" in workspace_dict:
        pre_tab_or_window = workspace_dict["pre_window"]
        if isinstance(pre_tab_or_window, list):
            pre_window_chain.extend(pre_tab_or_window)
        else:
            pre_window_chain.append(pre_tab_or_window)
    if pre_window_chain:
        tmuxp_workspace["shell_command_before"] = pre_window_chain

    for window_dict in workspace_dict["windows"]:
        for k, v in window_dict.items():
            window_dict = {"window_name": k}

            if isinstance(v, str) or v is None:
                window_dict["panes"] = [v]
                tmuxp_workspace["windows"].append(window_dict)
                continue
            if isinstance(v, list):
                window_dict["panes"] = v
                tmuxp_workspace["windows"].append(window_dict)
                continue

            if "pre" in v:
                window_dict["shell_command_before"] = v["pre"]
            if "panes" in v:
                window_dict["panes"] = v["panes"]
            if "root" in v:
                window_dict["start_directory"] = v["root"]

            if "layout" in v:
                window_dict["layout"] = v["layout"]
            # pass synchronize through (true/before/after) — same key name.
            if "synchronize" in v:
                window_dict["synchronize"] = v["synchronize"]
            tmuxp_workspace["windows"].append(window_dict)

    _apply_tmuxinator_startup_focus(workspace_dict, tmuxp_workspace)
    return tmuxp_workspace


def _apply_tmuxinator_startup_focus(
    workspace_dict: dict[str, t.Any],
    tmuxp_workspace: dict[str, t.Any],
) -> None:
    """Map tmuxinator `startup_window`/`startup_pane` to tmuxp `focus: true`.

    tmuxinator passes these values directly to tmux as targets
    (`project.rb:261-267`); a string is a window name, an integer is an
    index. tmuxp uses a per-window/per-pane `focus` flag instead. We
    resolve the value (try int first, fall back to name) and set `focus:
    true` on the matching window (and pane). Unresolved values warn.
    """
    windows = tmuxp_workspace.get("windows", [])

    target_window_idx: int | None = None
    if "startup_window" in workspace_dict:
        target_window_idx = _resolve_startup_index(
            workspace_dict["startup_window"],
            windows,
            "window_name",
            "startup_window",
            tmuxp_workspace.get("session_name"),
        )
        if target_window_idx is not None:
            windows[target_window_idx]["focus"] = True

    if "startup_pane" in workspace_dict and target_window_idx is not None:
        panes = windows[target_window_idx].get("panes") or []
        # Pane lists in this importer are positional strings; we can't add
        # a `focus` flag without converting. Skip unless panes are dicts.
        normalized_panes: list[t.Any] = []
        pane_target = _resolve_startup_index(
            workspace_dict["startup_pane"],
            panes,
            None,
            "startup_pane",
            tmuxp_workspace.get("session_name"),
        )
        for idx, pane in enumerate(panes):
            if idx == pane_target:
                if isinstance(pane, dict):
                    normalized_panes.append({**pane, "focus": True})
                else:
                    normalized_panes.append(
                        {"shell_command": [pane] if pane else [], "focus": True},
                    )
            else:
                normalized_panes.append(pane)
        windows[target_window_idx]["panes"] = normalized_panes


def _resolve_startup_index(
    value: t.Any,
    items: list[t.Any],
    name_key: str | None,
    field: str,
    session_name: str | None,
) -> int | None:
    """Resolve a tmuxinator startup_window/startup_pane value to a list index.

    Tries integer first (treated as 0-based index into ``items``), then
    falls back to matching by ``name_key`` if provided. Returns None and
    warns if no match.

    >>> windows = [{"window_name": "shell"}, {"window_name": "editor"}]
    >>> _resolve_startup_index(0, windows, "window_name", "f", None)
    0
    >>> _resolve_startup_index("editor", windows, "window_name", "f", None)
    1
    >>> _resolve_startup_index("missing", windows, "window_name", "f", None) is None
    True
    """
    try:
        idx = int(value)
    except (TypeError, ValueError):
        idx = None
    if idx is not None and 0 <= idx < len(items):
        return idx
    if name_key is not None:
        for i, item in enumerate(items):
            if isinstance(item, dict) and item.get(name_key) == value:
                return i
    logger.warning(
        "%s value did not match any window/pane",
        field,
        extra={
            "tmux_key": field,
            "tmux_session": session_name,
        },
    )
    return None


def import_teamocil(workspace_dict: dict[str, t.Any]) -> dict[str, t.Any]:
    """Return tmuxp workspace from a `teamocil`_ yaml workspace.

    .. _teamocil: https://github.com/remiprev/teamocil

    Detects the teamocil format and dispatches:

    - **v0.x** (pre-1.0): ``session:`` wrapper present. Handles
      ``splits``/``cmd``/``filters``/``clear``/``with_env_var``/
      ``cmd_separator``.
    - **v1.x** (1.0-1.4.2): top-level ``windows``. Handles ``commands``,
      string pane shorthand, per-window/pane ``focus``, window
      ``options``.

    Parameters
    ----------
    workspace_dict : dict
        python dict for tmuxp workspace

    Notes
    -----
    Behavior of v0.x-only keys:

    - ``with_env_var`` (default ``true`` in v0.x) maps to a session-level
      ``environment: {TEAMOCIL: "1"}`` to mirror teamocil 0.4-stable.
    - ``clear`` is preserved on the window dict but the builder does not
      yet act on it; a warning is emitted.
    - ``cmd_separator`` is irrelevant since tmuxp sends commands
      individually; a warning is emitted.
    - ``width``/``height``/``target`` (per-pane geometry) are dropped
      with a warning; builder support is a separate change.
    """
    # Top-level shallow copy so the dispatch helpers' .pop()s don't mutate
    # the caller's dict. Nested window/pane dicts are still mutated in place
    # by the v0.x window loop; deepcopy upstream if you share nested values.
    workspace_dict = {**workspace_dict}
    has_session_wrapper = "session" in workspace_dict
    inner = workspace_dict["session"] if has_session_wrapper else workspace_dict
    is_v0x = has_session_wrapper or _has_v0x_window_markers(inner)
    logger.debug(
        "importing teamocil workspace",
        extra={
            "tmux_session": inner.get("name", ""),
            "tmux_importer_version": "v0.x" if is_v0x else "v1.x",
        },
    )
    if is_v0x:
        return _import_teamocil_v0x(inner)
    return _import_teamocil_v1x(workspace_dict)


def _has_v0x_window_markers(inner: dict[str, t.Any]) -> bool:
    """Return True if any window/pane uses a v0.x-only key.

    Some v0.x configs in the wild omit the ``session:`` wrapper but still
    use ``splits`` (v0.x pane key), ``cmd`` (v0.x command key), or
    ``filters`` (v0.x before/after hooks). Detect those so they route to
    the v0.x importer instead of being misclassified as v1.x.
    """
    for w in inner.get("windows", []) or []:
        if not isinstance(w, dict):
            continue
        if "splits" in w or "filters" in w:
            return True
        for pane in w.get("panes", []) or []:
            if isinstance(pane, dict) and "cmd" in pane:
                return True
    return False


def _import_teamocil_v0x(workspace_dict: dict[str, t.Any]) -> dict[str, t.Any]:
    """Convert a teamocil v0.x workspace (``session:`` wrapped) to tmuxp."""
    tmuxp_workspace: dict[str, t.Any] = {
        "session_name": workspace_dict.get("name"),
    }

    if "root" in workspace_dict:
        tmuxp_workspace["start_directory"] = workspace_dict.pop("root")

    # v0.x default: TEAMOCIL=1 is exported in every pane (with_env_var=true
    # by default per teamocil 0.4-stable). _is_falsy_yaml handles quoted
    # YAML strings like with_env_var: "false" that survive to Python as
    # truthy strings. We're already in the v0.x helper so no is_v0x check.
    if not _is_falsy_yaml(workspace_dict.get("with_env_var", True)):
        tmuxp_workspace.setdefault("environment", {})["TEAMOCIL"] = "1"

    if "cmd_separator" in workspace_dict:
        logger.warning(
            "cmd_separator has no effect in tmuxp; commands are sent individually",
            extra={
                "tmux_key": "cmd_separator",
                "tmux_session": tmuxp_workspace.get("session_name"),
            },
        )

    tmuxp_workspace["windows"] = []

    for w in workspace_dict["windows"]:
        window_dict: dict[str, t.Any] = {"window_name": w["name"]}

        if "clear" in w:
            window_dict["clear"] = w["clear"]
            logger.warning(
                "clear is preserved on the window but the builder does not "
                "yet act on it",
                extra={
                    "tmux_key": "clear",
                    "tmux_session": tmuxp_workspace.get("session_name"),
                },
            )

        if "filters" in w:
            if "before" in w["filters"]:
                window_dict["shell_command_before"] = w["filters"]["before"]
            if "after" in w["filters"]:
                window_dict["shell_command_after"] = w["filters"]["after"]

        if "root" in w:
            window_dict["start_directory"] = w.pop("root")

        if "splits" in w:
            w["panes"] = w.pop("splits")

        if "panes" in w:
            for p in w["panes"]:
                if "cmd" in p:
                    p["shell_command"] = p.pop("cmd")
                for geom_key in ("width", "height", "target"):
                    if geom_key in p:
                        # No builder support for per-pane geometry yet
                        # (libtmux Pane.split(target=...) and Pane.resize()
                        # exist but the builder doesn't wire them up).
                        p.pop(geom_key)
                        logger.warning(
                            "v0.x pane key dropped (no per-pane geometry "
                            "support in tmuxp)",
                            extra={
                                "tmux_key": geom_key,
                                "tmux_session": tmuxp_workspace.get(
                                    "session_name",
                                ),
                            },
                        )
            window_dict["panes"] = w["panes"]

        if "layout" in w:
            window_dict["layout"] = w["layout"]
        tmuxp_workspace["windows"].append(window_dict)

    return tmuxp_workspace


def _import_teamocil_v1x(workspace_dict: dict[str, t.Any]) -> dict[str, t.Any]:
    """Convert a teamocil v1.x workspace (top-level ``windows``) to tmuxp.

    v1.x dropped the ``session:`` wrapper, ``filters``, ``with_env_var``,
    and ``cmd_separator``. A bare string pane is shorthand for
    ``{commands: [<string>]}`` (window.rb:12-14 in upstream teamocil).
    """
    tmuxp_workspace: dict[str, t.Any] = {
        "session_name": workspace_dict.get("name"),
    }

    if "root" in workspace_dict:
        tmuxp_workspace["start_directory"] = workspace_dict["root"]

    tmuxp_workspace["windows"] = []
    for w in workspace_dict.get("windows", []):
        window_dict: dict[str, t.Any] = {"window_name": w["name"]}
        if "root" in w:
            window_dict["start_directory"] = w["root"]
        if "layout" in w:
            window_dict["layout"] = w["layout"]
        if "focus" in w:
            window_dict["focus"] = w["focus"]
        if "options" in w:
            window_dict["options"] = w["options"]
        window_dict["panes"] = [_normalize_v1x_pane(p) for p in w.get("panes", [])]
        tmuxp_workspace["windows"].append(window_dict)

    return tmuxp_workspace


def _normalize_v1x_pane(pane: t.Any) -> dict[str, t.Any]:
    """Normalize a teamocil v1.x pane (string or dict) to tmuxp pane dict.

    >>> _normalize_v1x_pane("vim")
    {'shell_command': ['vim']}
    >>> _normalize_v1x_pane({"commands": ["a", "b"], "focus": True})
    {'shell_command': ['a', 'b'], 'focus': True}
    """
    if isinstance(pane, str):
        return {"shell_command": [pane]}
    out: dict[str, t.Any] = {}
    if "commands" in pane:
        out["shell_command"] = pane["commands"]
    if "focus" in pane:
        out["focus"] = pane["focus"]
    if not out and isinstance(pane, dict) and pane:
        # Dict had keys, but none we recognized — surface to user instead
        # of silently producing a no-command pane.
        logger.warning(
            "v1.x pane dict has no recognizable keys; produced empty pane",
            extra={"tmux_key": ",".join(sorted(pane.keys()))},
        )
    return out
