"""CLI utility helpers for tmuxp."""

from __future__ import annotations

import typing as t

from tmuxp._internal.colors import (
    ColorMode,
    Colors,
    UnknownStyleColor,
    strip_ansi,
    style,
    unstyle,
)
from tmuxp._internal.private_path import PrivatePath
from tmuxp.log import tmuxp_echo

if t.TYPE_CHECKING:
    from collections.abc import Callable, Sequence

# Re-export for backward compatibility
__all__ = [
    "ColorMode",
    "Colors",
    "UnknownStyleColor",
    "prompt",
    "prompt_bool",
    "prompt_choices",
    "prompt_yes_no",
    "strip_ansi",
    "style",
    "tmuxp_echo",
    "unstyle",
]


def prompt(
    name: str,
    default: str | None = None,
    value_proc: Callable[[str], str] | None = None,
    *,
    color_mode: ColorMode | None = None,
) -> str:
    """Return user input from command line.

    Parameters
    ----------
    name :
        prompt text
    default :
        default value if no input provided.
    color_mode :
        color mode for prompt styling. Defaults to AUTO if not specified.

    Returns
    -------
    str

    See Also
    --------
    :meth:`~prompt`, :meth:`~prompt_bool` and :meth:`~prompt_choices` are from
    `flask-script <https://github.com/techniq/flask-script>`_. See the
    `flask-script license <https://github.com/techniq/flask-script/blob/master/LICENSE>`_.
    """
    colors = Colors(color_mode if color_mode is not None else ColorMode.AUTO)
    # Use PrivatePath to mask home directory in displayed default
    display_default = str(PrivatePath(default)) if default else None
    prompt_ = name + (
        (display_default and " " + colors.info(f"[{display_default}]")) or ""
    )
    prompt_ += (name.endswith("?") and " ") or ": "
    while True:
        rv = input(prompt_) or default
        # Validate with value_proc only if we have a string value
        if rv is not None and value_proc is not None and callable(value_proc):
            try:
                value_proc(rv)
            except ValueError as e:
                return prompt(
                    str(e),
                    default=default,
                    value_proc=value_proc,
                    color_mode=color_mode,
                )

        if rv:
            return rv
        if default is not None:
            return default
        # No input and no default - loop to re-prompt


def prompt_bool(
    name: str,
    default: bool = False,
    yes_choices: Sequence[t.Any] | None = None,
    no_choices: Sequence[t.Any] | None = None,
    *,
    color_mode: ColorMode | None = None,
) -> bool:
    """Return True / False by prompting user input from command line.

    Parameters
    ----------
    name :
        prompt text
    default :
        default value if no input provided.
    yes_choices :
        default 'y', 'yes', '1', 'on', 'true', 't'
    no_choices :
        default 'n', 'no', '0', 'off', 'false', 'f'
    color_mode :
        color mode for prompt styling. Defaults to AUTO if not specified.

    Returns
    -------
    bool
    """
    colors = Colors(color_mode if color_mode is not None else ColorMode.AUTO)
    yes_choices = yes_choices or ("y", "yes", "1", "on", "true", "t")
    no_choices = no_choices or ("n", "no", "0", "off", "false", "f")

    if default is None:
        prompt_choice = "y/n"
    elif default is True:
        prompt_choice = "Y/n"
    else:
        prompt_choice = "y/N"

    prompt_ = name + " " + colors.muted(f"[{prompt_choice}]")
    prompt_ += (name.endswith("?") and " ") or ": "

    while True:
        rv = input(prompt_)
        if not rv:
            return default
        if rv.lower() in yes_choices:
            return True
        if rv.lower() in no_choices:
            return False


def prompt_yes_no(
    name: str,
    default: bool = True,
    *,
    color_mode: ColorMode | None = None,
) -> bool:
    """:meth:`prompt_bool()` returning yes by default.

    Parameters
    ----------
    name :
        prompt text
    default :
        default value if no input provided.
    color_mode :
        color mode for prompt styling. Defaults to AUTO if not specified.
    """
    return prompt_bool(name, default=default, color_mode=color_mode)


def prompt_choices(
    name: str,
    choices: Sequence[str | tuple[str, str]],
    default: str | None = None,
    no_choice: Sequence[str] = ("none",),
    *,
    color_mode: ColorMode | None = None,
) -> str | None:
    """Return user input from command line from set of provided choices.

    Parameters
    ----------
    name :
        prompt text
    choices :
        Sequence of available choices. Each choice may be a single string or
        a (key, value) tuple where key is used for matching.
    default :
        default value if no input provided.
    no_choice :
        acceptable list of strings for "null choice"
    color_mode :
        color mode for prompt styling. Defaults to AUTO if not specified.

    Returns
    -------
    str
    """
    colors = Colors(color_mode if color_mode is not None else ColorMode.AUTO)
    choices_: list[str] = []
    options: list[str] = []

    for choice in choices:
        if isinstance(choice, str):
            options.append(choice)
        elif isinstance(choice, tuple):
            options.append(f"{choice} [{choice[0]}]")
            choice = choice[0]
        choices_.append(choice)

    choices_str = colors.muted(f"({', '.join(options)})")
    default_str = " " + colors.info(f"[{default}]") if default else ""
    prompt_text = f"{name} - {choices_str}{default_str}"

    while True:
        prompt_ = prompt_text + ": "
        rv = input(prompt_) or default
        if not rv or rv == default:
            return default
        rv = rv.lower()
        if rv in no_choice:
            return None
        if rv in choices_:
            return rv
        print(
            colors.warning(f"Invalid choice '{rv}'. ")
            + f"Please choose from: {', '.join(choices_)}"
        )
