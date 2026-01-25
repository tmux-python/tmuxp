"""Custom docutils node types for argparse documentation.

This module defines custom node types that represent the structure of
CLI documentation, along with HTML visitor functions for rendering.
"""

from __future__ import annotations

import typing as t

from docutils import nodes

if t.TYPE_CHECKING:
    from sphinx.writers.html5 import HTML5Translator

# Import the lexer - use absolute import from parent package
import pathlib
import sys

# Add parent directory to path for lexer import
_ext_dir = pathlib.Path(__file__).parent.parent
if str(_ext_dir) not in sys.path:
    sys.path.insert(0, str(_ext_dir))

from argparse_lexer import ArgparseUsageLexer  # noqa: E402
from sphinx_argparse_neo.utils import strip_ansi  # noqa: E402


def _generate_argument_id(names: list[str], id_prefix: str = "") -> str:
    """Generate unique ID for an argument based on its names.

    Creates a slug-style ID suitable for HTML anchors by:
    1. Stripping leading dashes from option names
    2. Joining multiple names with hyphens
    3. Prepending optional prefix for namespace isolation

    Parameters
    ----------
    names : list[str]
        List of argument names (e.g., ["-L", "--socket-name"]).
    id_prefix : str
        Optional prefix for uniqueness (e.g., "shell" -> "shell-L-socket-name").

    Returns
    -------
    str
        A slug-style ID suitable for HTML anchors.

    Examples
    --------
    >>> _generate_argument_id(["-L"])
    'L'
    >>> _generate_argument_id(["--help"])
    'help'
    >>> _generate_argument_id(["-v", "--verbose"])
    'v-verbose'
    >>> _generate_argument_id(["-L"], "shell")
    'shell-L'
    >>> _generate_argument_id(["filename"])
    'filename'
    >>> _generate_argument_id([])
    ''
    """
    clean_names = [name.lstrip("-") for name in names if name.lstrip("-")]
    if not clean_names:
        return ""
    name_part = "-".join(clean_names)
    return f"{id_prefix}-{name_part}" if id_prefix else name_part


def _token_to_css_class(token_type: t.Any) -> str:
    """Map a Pygments token type to its CSS class abbreviation.

    Pygments uses hierarchical token names like Token.Name.Attribute.
    These map to CSS classes using abbreviations of the last two parts:
    - Token.Name.Attribute → 'na' (Name.Attribute)
    - Token.Generic.Heading → 'gh' (Generic.Heading)
    - Token.Punctuation → 'p' (just Punctuation)

    Parameters
    ----------
    token_type : Any
        A Pygments token type (from pygments.token).

    Returns
    -------
    str
        CSS class abbreviation, or empty string if not mappable.

    Examples
    --------
    >>> from pygments.token import Token
    >>> _token_to_css_class(Token.Name.Attribute)
    'na'
    >>> _token_to_css_class(Token.Generic.Heading)
    'gh'
    >>> _token_to_css_class(Token.Punctuation)
    'p'
    >>> _token_to_css_class(Token.Text.Whitespace)
    'tw'
    """
    type_str = str(token_type)
    # Token string looks like "Token.Name.Attribute" or "Token.Punctuation"
    parts = type_str.split(".")

    if len(parts) >= 3:
        # Token.Name.Attribute -> "na" (first char of each of last two parts)
        return parts[-2][0].lower() + parts[-1][0].lower()
    elif len(parts) == 2:
        # Token.Punctuation -> "p" (first char of last part)
        return parts[-1][0].lower()
    return ""


def _highlight_usage(usage_text: str, encode: t.Callable[[str], str]) -> str:
    """Tokenize usage text and wrap tokens in highlighted span elements.

    Uses ArgparseUsageLexer to tokenize the usage string, then wraps each
    token in a <span> with the appropriate CSS class for styling.

    Parameters
    ----------
    usage_text : str
        The usage string to highlight (should include "usage: " prefix).
    encode : Callable[[str], str]
        HTML encoding function (typically translator.encode).

    Returns
    -------
    str
        HTML string with tokens wrapped in styled <span> elements.

    Examples
    --------
    >>> def mock_encode(s: str) -> str:
    ...     return s.replace("&", "&amp;").replace("<", "&lt;")
    >>> html = _highlight_usage("usage: cmd [-h]", mock_encode)
    >>> '<span class="gh">usage:</span>' in html
    True
    >>> '<span class="nl">cmd</span>' in html
    True
    >>> '<span class="na">-h</span>' in html
    True
    """
    lexer = ArgparseUsageLexer()
    parts: list[str] = []

    for tok_type, tok_value in lexer.get_tokens(usage_text):
        if not tok_value:
            continue

        css_class = _token_to_css_class(tok_type)
        escaped = encode(tok_value)
        type_str = str(tok_type).lower()

        # Skip wrapping for whitespace and plain text tokens
        if css_class and "whitespace" not in type_str and "text" not in type_str:
            parts.append(f'<span class="{css_class}">{escaped}</span>')
        else:
            parts.append(escaped)

    return "".join(parts)


def _highlight_argument_names(
    names: list[str], metavar: str | None, encode: t.Callable[[str], str]
) -> str:
    """Highlight argument names and metavar with appropriate CSS classes.

    Short options (-h) get class 'na' (Name.Attribute).
    Long options (--help) get class 'nt' (Name.Tag).
    Positional arguments get class 'nl' (Name.Label).
    Metavars get class 'nv' (Name.Variable).

    Parameters
    ----------
    names : list[str]
        List of argument names (e.g., ["-v", "--verbose"]).
    metavar : str | None
        Optional metavar (e.g., "FILE", "PATH").
    encode : Callable[[str], str]
        HTML encoding function.

    Returns
    -------
    str
        HTML string with highlighted argument signature.

    Examples
    --------
    >>> def mock_encode(s: str) -> str:
    ...     return s
    >>> html = _highlight_argument_names(["-h", "--help"], None, mock_encode)
    >>> '<span class="na">-h</span>' in html
    True
    >>> '<span class="nt">--help</span>' in html
    True
    >>> html = _highlight_argument_names(["--output"], "FILE", mock_encode)
    >>> '<span class="nv">FILE</span>' in html
    True
    >>> html = _highlight_argument_names(["sync"], None, mock_encode)
    >>> '<span class="nl">sync</span>' in html
    True
    """
    sig_parts: list[str] = []

    for name in names:
        escaped = encode(name)
        if name.startswith("--"):
            sig_parts.append(f'<span class="nt">{escaped}</span>')
        elif name.startswith("-"):
            sig_parts.append(f'<span class="na">{escaped}</span>')
        else:
            # Positional argument or subcommand
            sig_parts.append(f'<span class="nl">{escaped}</span>')

    result = ", ".join(sig_parts)

    if metavar:
        escaped_metavar = encode(metavar)
        result = f'{result} <span class="nv">{escaped_metavar}</span>'

    return result


class argparse_program(nodes.General, nodes.Element):
    """Root node for an argparse program documentation block.

    Attributes
    ----------
    prog : str
        The program name.

    Examples
    --------
    >>> node = argparse_program()
    >>> node["prog"] = "myapp"
    >>> node["prog"]
    'myapp'
    """

    pass


class argparse_usage(nodes.General, nodes.Element):
    """Node for displaying program usage.

    Contains the usage string as a literal block.

    Examples
    --------
    >>> node = argparse_usage()
    >>> node["usage"] = "myapp [-h] [--verbose] command"
    >>> node["usage"]
    'myapp [-h] [--verbose] command'
    """

    pass


class argparse_group(nodes.General, nodes.Element):
    """Node for an argument group (positional, optional, or custom).

    Attributes
    ----------
    title : str
        The group title.
    description : str | None
        Optional group description.

    Examples
    --------
    >>> node = argparse_group()
    >>> node["title"] = "Output Options"
    >>> node["title"]
    'Output Options'
    """

    pass


class argparse_argument(nodes.Part, nodes.Element):
    """Node for a single CLI argument.

    Attributes
    ----------
    names : list[str]
        Argument names/flags.
    help : str | None
        Help text.
    default : str | None
        Default value string.
    choices : list[str] | None
        Available choices.
    required : bool
        Whether the argument is required.
    metavar : str | None
        Metavar for display.

    Examples
    --------
    >>> node = argparse_argument()
    >>> node["names"] = ["-v", "--verbose"]
    >>> node["names"]
    ['-v', '--verbose']
    """

    pass


class argparse_subcommands(nodes.General, nodes.Element):
    """Container node for subcommands section.

    Examples
    --------
    >>> node = argparse_subcommands()
    >>> node["title"] = "Commands"
    >>> node["title"]
    'Commands'
    """

    pass


class argparse_subcommand(nodes.General, nodes.Element):
    """Node for a single subcommand.

    Attributes
    ----------
    name : str
        Subcommand name.
    aliases : list[str]
        Subcommand aliases.
    help : str | None
        Subcommand help text.

    Examples
    --------
    >>> node = argparse_subcommand()
    >>> node["name"] = "sync"
    >>> node["aliases"] = ["s"]
    >>> node["name"]
    'sync'
    """

    pass


# HTML Visitor Functions


def visit_argparse_program_html(self: HTML5Translator, node: argparse_program) -> None:
    """Visit argparse_program node - start program container.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_program
        The program node being visited.
    """
    prog = node.get("prog", "")
    self.body.append(f'<div class="argparse-program" data-prog="{prog}">\n')


def depart_argparse_program_html(self: HTML5Translator, node: argparse_program) -> None:
    """Depart argparse_program node - close program container.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_program
        The program node being departed.
    """
    self.body.append("</div>\n")


def visit_argparse_usage_html(self: HTML5Translator, node: argparse_usage) -> None:
    """Visit argparse_usage node - render usage block with syntax highlighting.

    The usage text is tokenized using ArgparseUsageLexer and wrapped in
    styled <span> elements for semantic highlighting of options, metavars,
    commands, and punctuation.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_usage
        The usage node being visited.
    """
    usage = strip_ansi(node.get("usage", ""))
    # Add both argparse-usage class and highlight class for CSS targeting
    self.body.append('<pre class="argparse-usage highlight-argparse-usage">')
    # Prepend "usage: " and highlight the full usage string
    highlighted = _highlight_usage(f"usage: {usage}", self.encode)
    self.body.append(highlighted)


def depart_argparse_usage_html(self: HTML5Translator, node: argparse_usage) -> None:
    """Depart argparse_usage node - close usage block.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_usage
        The usage node being departed.
    """
    self.body.append("</pre>\n")


def visit_argparse_group_html(self: HTML5Translator, node: argparse_group) -> None:
    """Visit argparse_group node - start argument group.

    The title is now rendered by the parent section node, so this visitor
    only handles the group container and description.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_group
        The group node being visited.
    """
    title = node.get("title", "")
    group_id = title.lower().replace(" ", "-") if title else "arguments"
    self.body.append(f'<div class="argparse-group" data-group="{group_id}">\n')
    # Title rendering removed - parent section now provides the heading
    description = node.get("description")
    if description:
        self.body.append(
            f'<p class="argparse-group-description">{self.encode(description)}</p>\n'
        )
    self.body.append('<dl class="argparse-arguments">\n')


def depart_argparse_group_html(self: HTML5Translator, node: argparse_group) -> None:
    """Depart argparse_group node - close argument group.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_group
        The group node being departed.
    """
    self.body.append("</dl>\n")
    self.body.append("</div>\n")


def visit_argparse_argument_html(
    self: HTML5Translator, node: argparse_argument
) -> None:
    """Visit argparse_argument node - render argument entry with highlighting.

    Argument names are highlighted with semantic CSS classes:
    - Short options (-h) get class 'na' (Name.Attribute)
    - Long options (--help) get class 'nt' (Name.Tag)
    - Positional arguments get class 'nl' (Name.Label)
    - Metavars get class 'nv' (Name.Variable)

    The argument is wrapped in a container div with a unique ID for linking.
    A headerlink anchor (¶) is added for direct navigation.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_argument
        The argument node being visited.
    """
    names: list[str] = node.get("names", [])
    metavar = node.get("metavar")
    id_prefix: str = node.get("id_prefix", "")

    # Generate unique ID for this argument
    arg_id = _generate_argument_id(names, id_prefix)

    # Open wrapper div with ID for linking
    if arg_id:
        self.body.append(f'<div class="argparse-argument-wrapper" id="{arg_id}">\n')
    else:
        self.body.append('<div class="argparse-argument-wrapper">\n')

    # Build the argument signature with syntax highlighting
    highlighted_sig = _highlight_argument_names(names, metavar, self.encode)

    # Add headerlink anchor inside dt for navigation
    headerlink = ""
    if arg_id:
        headerlink = f'<a class="headerlink" href="#{arg_id}">¶</a>'

    self.body.append(
        f'<dt class="argparse-argument-name">{highlighted_sig}{headerlink}</dt>\n'
    )
    self.body.append('<dd class="argparse-argument-help">')

    # Add help text
    help_text = node.get("help")
    if help_text:
        self.body.append(f"<p>{self.encode(help_text)}</p>")


def depart_argparse_argument_html(
    self: HTML5Translator, node: argparse_argument
) -> None:
    """Depart argparse_argument node - close argument entry.

    Adds default, choices, and type information if present.
    Default values are wrapped in ``<span class="nv">`` for styled display.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_argument
        The argument node being departed.
    """
    # Build metadata as definition list items
    default = node.get("default_string")
    choices = node.get("choices")
    type_name = node.get("type_name")
    required = node.get("required", False)

    if default is not None or choices or type_name or required:
        self.body.append('<dl class="argparse-argument-meta">\n')

        if default is not None:
            self.body.append('<div class="argparse-meta-item">')
            self.body.append('<dt class="argparse-meta-key">Default</dt>')
            self.body.append(
                f'<dd class="argparse-meta-value">'
                f'<span class="nv">{self.encode(default)}</span></dd>'
            )
            self.body.append("</div>\n")

        if type_name:
            self.body.append('<div class="argparse-meta-item">')
            self.body.append('<dt class="argparse-meta-key">Type</dt>')
            self.body.append(
                f'<dd class="argparse-meta-value">'
                f'<span class="nv">{self.encode(type_name)}</span></dd>'
            )
            self.body.append("</div>\n")

        if choices:
            choices_str = ", ".join(str(c) for c in choices)
            self.body.append('<div class="argparse-meta-item">')
            self.body.append('<dt class="argparse-meta-key">Choices</dt>')
            self.body.append(
                f'<dd class="argparse-meta-value">{self.encode(choices_str)}</dd>'
            )
            self.body.append("</div>\n")

        if required:
            self.body.append('<dt class="argparse-meta-tag">Required</dt>\n')

        self.body.append("</dl>\n")

    self.body.append("</dd>\n")
    # Close wrapper div
    self.body.append("</div>\n")


def visit_argparse_subcommands_html(
    self: HTML5Translator, node: argparse_subcommands
) -> None:
    """Visit argparse_subcommands node - start subcommands section.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_subcommands
        The subcommands node being visited.
    """
    title = node.get("title", "Sub-commands")
    self.body.append('<div class="argparse-subcommands">\n')
    self.body.append(
        f'<p class="argparse-subcommands-title">{self.encode(title)}</p>\n'
    )


def depart_argparse_subcommands_html(
    self: HTML5Translator, node: argparse_subcommands
) -> None:
    """Depart argparse_subcommands node - close subcommands section.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_subcommands
        The subcommands node being departed.
    """
    self.body.append("</div>\n")


def visit_argparse_subcommand_html(
    self: HTML5Translator, node: argparse_subcommand
) -> None:
    """Visit argparse_subcommand node - start subcommand entry.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_subcommand
        The subcommand node being visited.
    """
    name = node.get("name", "")
    aliases: list[str] = node.get("aliases", [])

    self.body.append(f'<div class="argparse-subcommand" data-name="{name}">\n')

    # Subcommand header
    header = name
    if aliases:
        alias_str = ", ".join(aliases)
        header = f"{name} ({alias_str})"
    self.body.append(
        f'<h4 class="argparse-subcommand-name">{self.encode(header)}</h4>\n'
    )

    # Help text
    help_text = node.get("help")
    if help_text:
        self.body.append(
            f'<p class="argparse-subcommand-help">{self.encode(help_text)}</p>\n'
        )


def depart_argparse_subcommand_html(
    self: HTML5Translator, node: argparse_subcommand
) -> None:
    """Depart argparse_subcommand node - close subcommand entry.

    Parameters
    ----------
    self : HTML5Translator
        The Sphinx HTML translator.
    node : argparse_subcommand
        The subcommand node being departed.
    """
    self.body.append("</div>\n")
