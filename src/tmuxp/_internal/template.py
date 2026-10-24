"""Minimal template engine for tmuxp workspace files.

Two substitution forms only — keep the surface small and predictable:

- ``${name}``           — required variable; raises in strict mode if missing
- ``${name:-default}``  — optional, falls back to the literal default text

Bare ``$name`` is intentionally NOT supported: the post-parse expansion in
:func:`tmuxp.workspace.loader.expandshell` already handles ``$ENV_VAR``
forms on specific config keys. Keeping this engine tied to ``${...}`` lets
the two layers cohabit without ambiguity.

Templating runs on the raw YAML text before
:class:`tmuxp._internal.config_reader.ConfigReader` parses it,
mirroring tmuxinator's ERB-before-YAML behaviour.

This module deliberately has no runtime dependencies beyond :mod:`re`.
"""

from __future__ import annotations

import re
import typing as t

__all__ = [
    "UnresolvedVariableError",
    "parse_cli_vars",
    "render",
]

_VAR_PATTERN = re.compile(
    r"""
    \$\{                                  # opening ${
    (?P<name>[A-Za-z_][A-Za-z0-9_]*)      # variable name
    (?:                                   # optional default group
        :-                                # default operator
        (?P<default>[^}]*)                # default value (no nested braces)
    )?
    \}                                    # closing }
    """,
    re.VERBOSE,
)


class UnresolvedVariableError(KeyError):
    """A template referenced a variable with no value and no default.

    Subclass of :class:`KeyError` so callers using ``except KeyError`` keep
    working, but the more specific name lets tmuxp's CLI distinguish this
    from an actual dict-key miss.
    """


def render(
    template: str,
    variables: t.Mapping[str, str],
    *,
    strict: bool = True,
) -> str:
    """Substitute ``${name}`` and ``${name:-default}`` placeholders.

    Parameters
    ----------
    template : str
        The raw text containing placeholders.
    variables : Mapping[str, str]
        Substitution dictionary (typically from CLI ``KEY=VALUE`` args).
    strict : bool, optional
        When ``True`` (the default), an unresolved placeholder without a
        default raises :class:`UnresolvedVariableError`. When ``False``,
        unresolved placeholders are left in the output untouched — useful
        when a later pipeline stage (e.g. ``loader.expandshell``) will
        resolve them.

    Returns
    -------
    str
        The rendered template.

    >>> render("hello ${name}", {"name": "world"})
    'hello world'
    >>> render("port=${port:-3000}", {})
    'port=3000'
    >>> render("port=${port:-3000}", {"port": "4000"})
    'port=4000'
    >>> render("untouched ${HOME}", {}, strict=False)
    'untouched ${HOME}'
    """

    def replace(match: re.Match[str]) -> str:
        name = match["name"]
        if name in variables:
            return variables[name]
        default = match["default"]
        if default is not None:
            return default
        if strict:
            raise UnresolvedVariableError(name)
        return match[0]

    return _VAR_PATTERN.sub(replace, template)


def parse_cli_vars(args: t.Sequence[str]) -> dict[str, str]:
    """Parse ``KEY=VALUE`` positional CLI args into a dict.

    Supports values containing ``=``: only the first ``=`` is treated as
    the separator. Empty input returns an empty dict.

    Parameters
    ----------
    args : Sequence[str]
        Tokens from the CLI (e.g. ``["app=blog", "port=4000"]``).

    Returns
    -------
    dict[str, str]
        Variable map suitable for passing as ``variables=`` to
        :func:`render`.

    Raises
    ------
    ValueError
        If any token has no ``=`` separator.

    >>> parse_cli_vars(["app=blog", "port=4000"])
    {'app': 'blog', 'port': '4000'}
    >>> parse_cli_vars(["url=https://example.com/?a=1"])
    {'url': 'https://example.com/?a=1'}
    >>> parse_cli_vars([])
    {}
    """
    out: dict[str, str] = {}
    for token in args:
        if "=" not in token:
            msg = f"template var must be KEY=VALUE: {token!r}"
            raise ValueError(msg)
        key, _, value = token.partition("=")
        out[key] = value
    return out
