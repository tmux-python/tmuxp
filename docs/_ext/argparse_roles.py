"""Docutils inline roles for CLI/argparse highlighting.

This module provides custom docutils roles for inline highlighting of CLI
elements in reStructuredText and MyST documentation.

Available roles:
- :cli-option: - CLI options (--verbose, -h)
- :cli-metavar: - Metavar placeholders (FILE, PATH)
- :cli-command: - Command names (sync, add)
- :cli-default: - Default values (None, "default")
- :cli-choice: - Choice values (json, yaml)
"""

from __future__ import annotations

import typing as t

from docutils import nodes
from docutils.parsers.rst import roles

if t.TYPE_CHECKING:
    from docutils.parsers.rst.states import Inliner


def normalize_options(options: dict[str, t.Any] | None) -> dict[str, t.Any]:
    """Normalize role options, converting None to empty dict.

    Parameters
    ----------
    options : dict | None
        Options passed to the role.

    Returns
    -------
    dict
        Normalized options dict (never None).

    Examples
    --------
    >>> normalize_options(None)
    {}
    >>> normalize_options({"class": "custom"})
    {'class': 'custom'}
    """
    return options if options is not None else {}


def cli_option_role(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: Inliner | None,
    options: dict[str, t.Any] | None = None,
    content: list[str] | None = None,
) -> tuple[list[nodes.Node], list[nodes.system_message]]:
    """Role for CLI options like --foo or -h.

    Generates a literal node with appropriate CSS classes for styling.
    Long options (--foo) get 'cli-option-long', short options (-h) get
    'cli-option-short'.

    Parameters
    ----------
    name : str
        Local name of the role used in document.
    rawtext : str
        Full interpreted text including role markup.
    text : str
        Content between backticks.
    lineno : int
        Line number.
    inliner : Inliner | None
        Object that called the role (has .reporter, .document).
    options : dict | None
        Options from role directive.
    content : list | None
        Content from role directive.

    Returns
    -------
    tuple[list[nodes.Node], list[nodes.system_message]]
        Nodes to insert and any messages.

    Examples
    --------
    >>> node_list, messages = cli_option_role(
    ...     "cli-option", ":cli-option:`--verbose`", "--verbose",
    ...     1, None
    ... )
    >>> node_list[0]["classes"]
    ['cli-option', 'cli-option-long']

    >>> node_list, messages = cli_option_role(
    ...     "cli-option", ":cli-option:`-h`", "-h",
    ...     1, None
    ... )
    >>> node_list[0]["classes"]
    ['cli-option', 'cli-option-short']

    >>> node_list, messages = cli_option_role(
    ...     "cli-option", ":cli-option:`--no-color`", "--no-color",
    ...     1, None
    ... )
    >>> node_list[0].astext()
    '--no-color'
    """
    options = normalize_options(options)
    node = nodes.literal(rawtext, text, classes=["cli-option"])

    if text.startswith("--"):
        node["classes"].append("cli-option-long")
    elif text.startswith("-"):
        node["classes"].append("cli-option-short")

    return [node], []


def cli_metavar_role(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: Inliner | None,
    options: dict[str, t.Any] | None = None,
    content: list[str] | None = None,
) -> tuple[list[nodes.Node], list[nodes.system_message]]:
    """Role for CLI metavar placeholders like FILE or PATH.

    Generates a literal node with 'cli-metavar' CSS class for styling.

    Parameters
    ----------
    name : str
        Local name of the role used in document.
    rawtext : str
        Full interpreted text including role markup.
    text : str
        Content between backticks.
    lineno : int
        Line number.
    inliner : Inliner | None
        Object that called the role.
    options : dict | None
        Options from role directive.
    content : list | None
        Content from role directive.

    Returns
    -------
    tuple[list[nodes.Node], list[nodes.system_message]]
        Nodes to insert and any messages.

    Examples
    --------
    >>> node_list, messages = cli_metavar_role(
    ...     "cli-metavar", ":cli-metavar:`FILE`", "FILE",
    ...     1, None
    ... )
    >>> node_list[0]["classes"]
    ['cli-metavar']
    >>> node_list[0].astext()
    'FILE'

    >>> node_list, messages = cli_metavar_role(
    ...     "cli-metavar", ":cli-metavar:`PATH`", "PATH",
    ...     1, None
    ... )
    >>> "cli-metavar" in node_list[0]["classes"]
    True
    """
    options = normalize_options(options)
    node = nodes.literal(rawtext, text, classes=["cli-metavar"])
    return [node], []


def cli_command_role(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: Inliner | None,
    options: dict[str, t.Any] | None = None,
    content: list[str] | None = None,
) -> tuple[list[nodes.Node], list[nodes.system_message]]:
    """Role for CLI command names like sync or add.

    Generates a literal node with 'cli-command' CSS class for styling.

    Parameters
    ----------
    name : str
        Local name of the role used in document.
    rawtext : str
        Full interpreted text including role markup.
    text : str
        Content between backticks.
    lineno : int
        Line number.
    inliner : Inliner | None
        Object that called the role.
    options : dict | None
        Options from role directive.
    content : list | None
        Content from role directive.

    Returns
    -------
    tuple[list[nodes.Node], list[nodes.system_message]]
        Nodes to insert and any messages.

    Examples
    --------
    >>> node_list, messages = cli_command_role(
    ...     "cli-command", ":cli-command:`sync`", "sync",
    ...     1, None
    ... )
    >>> node_list[0]["classes"]
    ['cli-command']
    >>> node_list[0].astext()
    'sync'

    >>> node_list, messages = cli_command_role(
    ...     "cli-command", ":cli-command:`myapp`", "myapp",
    ...     1, None
    ... )
    >>> "cli-command" in node_list[0]["classes"]
    True
    """
    options = normalize_options(options)
    node = nodes.literal(rawtext, text, classes=["cli-command"])
    return [node], []


def cli_default_role(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: Inliner | None,
    options: dict[str, t.Any] | None = None,
    content: list[str] | None = None,
) -> tuple[list[nodes.Node], list[nodes.system_message]]:
    """Role for CLI default values like None or "default".

    Generates a literal node with 'cli-default' CSS class for styling.

    Parameters
    ----------
    name : str
        Local name of the role used in document.
    rawtext : str
        Full interpreted text including role markup.
    text : str
        Content between backticks.
    lineno : int
        Line number.
    inliner : Inliner | None
        Object that called the role.
    options : dict | None
        Options from role directive.
    content : list | None
        Content from role directive.

    Returns
    -------
    tuple[list[nodes.Node], list[nodes.system_message]]
        Nodes to insert and any messages.

    Examples
    --------
    >>> node_list, messages = cli_default_role(
    ...     "cli-default", ":cli-default:`None`", "None",
    ...     1, None
    ... )
    >>> node_list[0]["classes"]
    ['cli-default']
    >>> node_list[0].astext()
    'None'

    >>> node_list, messages = cli_default_role(
    ...     "cli-default", ':cli-default:`"auto"`', '"auto"',
    ...     1, None
    ... )
    >>> "cli-default" in node_list[0]["classes"]
    True
    """
    options = normalize_options(options)
    node = nodes.literal(rawtext, text, classes=["cli-default"])
    return [node], []


def cli_choice_role(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: Inliner | None,
    options: dict[str, t.Any] | None = None,
    content: list[str] | None = None,
) -> tuple[list[nodes.Node], list[nodes.system_message]]:
    """Role for CLI choice values like json or yaml.

    Generates a literal node with 'cli-choice' CSS class for styling.

    Parameters
    ----------
    name : str
        Local name of the role used in document.
    rawtext : str
        Full interpreted text including role markup.
    text : str
        Content between backticks.
    lineno : int
        Line number.
    inliner : Inliner | None
        Object that called the role.
    options : dict | None
        Options from role directive.
    content : list | None
        Content from role directive.

    Returns
    -------
    tuple[list[nodes.Node], list[nodes.system_message]]
        Nodes to insert and any messages.

    Examples
    --------
    >>> node_list, messages = cli_choice_role(
    ...     "cli-choice", ":cli-choice:`json`", "json",
    ...     1, None
    ... )
    >>> node_list[0]["classes"]
    ['cli-choice']
    >>> node_list[0].astext()
    'json'

    >>> node_list, messages = cli_choice_role(
    ...     "cli-choice", ":cli-choice:`yaml`", "yaml",
    ...     1, None
    ... )
    >>> "cli-choice" in node_list[0]["classes"]
    True
    """
    options = normalize_options(options)
    node = nodes.literal(rawtext, text, classes=["cli-choice"])
    return [node], []


def register_roles() -> None:
    """Register all CLI roles with docutils.

    This function registers the following roles:
    - cli-option: For CLI options (--verbose, -h)
    - cli-metavar: For metavar placeholders (FILE, PATH)
    - cli-command: For command names (sync, add)
    - cli-default: For default values (None, "default")
    - cli-choice: For choice values (json, yaml)

    Examples
    --------
    >>> register_roles()
    >>> # Roles are now available in docutils RST parsing
    """
    roles.register_local_role("cli-option", cli_option_role)  # type: ignore[arg-type]
    roles.register_local_role("cli-metavar", cli_metavar_role)  # type: ignore[arg-type]
    roles.register_local_role("cli-command", cli_command_role)  # type: ignore[arg-type]
    roles.register_local_role("cli-default", cli_default_role)  # type: ignore[arg-type]
    roles.register_local_role("cli-choice", cli_choice_role)  # type: ignore[arg-type]
