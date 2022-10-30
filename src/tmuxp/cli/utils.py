import logging
import re
import typing as t

from .. import log

logger = logging.getLogger(__name__)


def tmuxp_echo(
    message: t.Optional[str] = None,
    log_level: str = "INFO",
    style_log: bool = False,
) -> None:
    """
    Combines logging.log and click.echo
    """
    if message is None:
        return

    if style_log:
        logger.log(log.LOG_LEVELS[log_level], message)
    else:
        logger.log(log.LOG_LEVELS[log_level], unstyle(message))

    print(message)


def prompt(
    name: str,
    default: t.Any = None,
    value_proc: t.Optional[t.Callable[[str], str]] = None,
) -> t.Any:
    """Return user input from command line.
    :meth:`~prompt`, :meth:`~prompt_bool` and :meth:`prompt_choices` are from
    `flask-script`_. See the `flask-script license`_.
    .. _flask-script: https://github.com/techniq/flask-script
    .. _flask-script license:
        https://github.com/techniq/flask-script/blob/master/LICENSE
    :param name: prompt text
    :param default: default value if no input provided.
    :rtype: string
    """

    _prompt = name + (default and " [%s]" % default or "")
    _prompt += name.endswith("?") and " " or ": "
    while True:
        rv = input(_prompt) or default
        try:
            if value_proc is not None and callable(value_proc):
                assert isinstance(rv, str)
                value_proc(rv)
        except ValueError as e:
            return prompt(str(e), default=default, value_proc=value_proc)

        if rv:
            return rv
        if default is not None:
            return default


def prompt_bool(
    name: str,
    default: bool = False,
    yes_choices: t.Optional[t.Sequence[t.Any]] = None,
    no_choices: t.Optional[t.Sequence[t.Any]] = None,
) -> bool:
    """Return user input from command line and converts to boolean value.
    :param name: prompt text
    :param default: default value if no input provided.
    :param yes_choices: default 'y', 'yes', '1', 'on', 'true', 't'
    :param no_choices: default 'n', 'no', '0', 'off', 'false', 'f'
    :rtype: bool
    """

    yes_choices = yes_choices or ("y", "yes", "1", "on", "true", "t")
    no_choices = no_choices or ("n", "no", "0", "off", "false", "f")

    if default is None:
        prompt_choice = "y/n"
    elif default is True:
        prompt_choice = "Y/n"
    else:
        prompt_choice = "y/N"

    _prompt = name + " [%s]" % prompt_choice
    _prompt += name.endswith("?") and " " or ": "

    while True:
        rv = input(_prompt)
        if not rv:
            return default
        if rv.lower() in yes_choices:
            return True
        elif rv.lower() in no_choices:
            return False


def prompt_yes_no(name: str, default: bool = True) -> bool:
    """:meth:`prompt_bool()` returning yes by default."""
    return prompt_bool(name, default=default)


_C = t.TypeVar("_C")


def prompt_choices(
    name: str,
    choices: t.Union[t.List[_C], t.Tuple[str, _C]],
    default: t.Optional[_C] = None,
    no_choice: t.Sequence[str] = ("none",),
) -> t.Optional[_C]:
    """Return user input from command line from set of provided choices.
    :param name: prompt text
    :param choices: list or tuple of available choices. Choices may be
                    single strings or (key, value) tuples.
    :param default: default value if no input provided.
    :param no_choice: acceptable list of strings for "null choice"
    :rtype: str
    """

    _choices = []
    options = []

    for choice in choices:
        if isinstance(choice, str):
            options.append(choice)
        elif isinstance(choice, tuple):
            options.append("%s [%s]" % (choice, choice[0]))
            choice = choice[0]
        _choices.append(choice)

    while True:
        rv = prompt(name + " - (%s)" % ", ".join(options), default=default)
        if not rv or rv == default:
            return default
        rv = rv.lower()
        if rv in no_choice:
            return None
        if rv in _choices:
            return rv


_ansi_re = re.compile(r"\033\[[;?0-9]*[a-zA-Z]")


def strip_ansi(value: str) -> str:
    return _ansi_re.sub("", value)


_ansi_colors = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "reset": 39,
    "bright_black": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
}
_ansi_reset_all = "\033[0m"


def _interpret_color(
    color: t.Union[int, t.Tuple[int, int, int], str], offset: int = 0
) -> str:
    if isinstance(color, int):
        return f"{38 + offset};5;{color:d}"

    if isinstance(color, (tuple, list)):
        r, g, b = color
        return f"{38 + offset};2;{r:d};{g:d};{b:d}"

    return str(_ansi_colors[color] + offset)


def style(
    text: t.Any,
    fg: t.Optional[t.Union[int, t.Tuple[int, int, int], str]] = None,
    bg: t.Optional[t.Union[int, t.Tuple[int, int, int], str]] = None,
    bold: t.Optional[bool] = None,
    dim: t.Optional[bool] = None,
    underline: t.Optional[bool] = None,
    overline: t.Optional[bool] = None,
    italic: t.Optional[bool] = None,
    blink: t.Optional[bool] = None,
    reverse: t.Optional[bool] = None,
    strikethrough: t.Optional[bool] = None,
    reset: bool = True,
) -> str:
    """Credit: click"""
    if not isinstance(text, str):
        text = str(text)

    bits = []

    if fg:
        try:
            bits.append(f"\033[{_interpret_color(fg)}m")
        except KeyError:
            raise TypeError(f"Unknown color {fg!r}") from None

    if bg:
        try:
            bits.append(f"\033[{_interpret_color(bg, 10)}m")
        except KeyError:
            raise TypeError(f"Unknown color {bg!r}") from None

    if bold is not None:
        bits.append(f"\033[{1 if bold else 22}m")
    if dim is not None:
        bits.append(f"\033[{2 if dim else 22}m")
    if underline is not None:
        bits.append(f"\033[{4 if underline else 24}m")
    if overline is not None:
        bits.append(f"\033[{53 if overline else 55}m")
    if italic is not None:
        bits.append(f"\033[{3 if italic else 23}m")
    if blink is not None:
        bits.append(f"\033[{5 if blink else 25}m")
    if reverse is not None:
        bits.append(f"\033[{7 if reverse else 27}m")
    if strikethrough is not None:
        bits.append(f"\033[{9 if strikethrough else 29}m")
    bits.append(text)
    if reset:
        bits.append(_ansi_reset_all)
    return "".join(bits)


def unstyle(text: str) -> str:
    """Removes ANSI styling information from a string.  Usually it's not
    necessary to use this function as tmuxp_echo function will
    automatically remove styling if necessary.

    credit: click.

    :param text: the text to remove style information from.
    """
    return strip_ansi(text)
