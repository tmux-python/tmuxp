"""Tmux session freezing functionality for tmuxp."""
import typing as t

from libtmux.pane import Pane
from libtmux.session import Session

if t.TYPE_CHECKING:
    from libtmux.window import Window


def inline(workspace_dict: t.Dict[str, t.Any]) -> t.Any:
    """Return workspace with inlined shorthands. Opposite of :meth:`loader.expand`.

    Parameters
    ----------
    workspace_dict : dict

    Returns
    -------
    dict
        workspace with shorthands inlined.
    """
    if (
        "shell_command" in workspace_dict
        and isinstance(workspace_dict["shell_command"], list)
        and len(workspace_dict["shell_command"]) == 1
    ):
        workspace_dict["shell_command"] = workspace_dict["shell_command"][0]

        if len(workspace_dict.keys()) == 1:
            return workspace_dict["shell_command"]
    if (
        "shell_command_before" in workspace_dict
        and isinstance(workspace_dict["shell_command_before"], list)
        and len(workspace_dict["shell_command_before"]) == 1
    ):
        workspace_dict["shell_command_before"] = workspace_dict["shell_command_before"][
            0
        ]

    # recurse into window and pane workspace items
    if "windows" in workspace_dict:
        workspace_dict["windows"] = [
            inline(window) for window in workspace_dict["windows"]
        ]
    if "panes" in workspace_dict:
        workspace_dict["panes"] = [inline(pane) for pane in workspace_dict["panes"]]

    return workspace_dict


def freeze(session: Session) -> t.Dict[str, t.Any]:
    """Freeze live tmux session into a tmuxp workspacee.

    Parameters
    ----------
    session : :class:`libtmux.Session`
        session object

    Returns
    -------
    dict
        tmuxp compatible workspace
    """
    session_config: t.Dict[str, t.Any] = {
        "session_name": session.session_name,
        "windows": [],
    }

    for window in session.windows:
        window_config: t.Dict[str, t.Any] = {
            "options": window.show_window_options(),
            "window_name": window.name,
            "layout": window.window_layout,
            "panes": [],
        }

        if getattr(window, "window_active", "0") == "1":
            window_config["focus"] = "true"

        # If all panes have same path, set 'start_directory' instead
        # of using 'cd' shell commands.
        def pane_has_same_path(window: "Window", pane: Pane) -> bool:
            return window.panes[0].pane_current_path == pane.pane_current_path

        if all(pane_has_same_path(window=window, pane=pane) for pane in window.panes):
            window_config["start_directory"] = window.panes[0].pane_current_path

        for pane in window.panes:
            pane_config: t.Union[str, t.Dict[str, t.Any]] = {"shell_command": []}
            assert isinstance(pane_config, dict)

            if "start_directory" not in window_config and pane.pane_current_path:
                pane_config["shell_command"].append("cd " + pane.pane_current_path)

            if getattr(pane, "pane_active", "0") == "1":
                pane_config["focus"] = "true"

            current_cmd = pane.pane_current_command

            def filter_interpreters_and_shells(current_cmd: t.Optional[str]) -> bool:
                return current_cmd is not None and (
                    current_cmd.startswith("-")
                    or any(
                        current_cmd.endswith(cmd) for cmd in ["python", "ruby", "node"]
                    )
                )

            if filter_interpreters_and_shells(current_cmd=current_cmd):
                current_cmd = None

            if current_cmd:
                pane_config["shell_command"].append(current_cmd)
            else:
                if not len(pane_config["shell_command"]):
                    pane_config = "pane"

            window_config["panes"].append(pane_config)

        session_config["windows"].append(window_config)

    return session_config
