"""Pygments lexers for argparse help output.

This module provides custom Pygments lexers for highlighting argparse-generated
command-line help text, including usage lines, section headers, and full help output.

Three lexer classes are provided:
- ArgparseUsageLexer: For usage lines only
- ArgparseHelpLexer: For full -h output (delegates usage to ArgparseUsageLexer)
- ArgparseLexer: Smart auto-detecting wrapper
"""

from __future__ import annotations

from pygments.lexer import RegexLexer, bygroups, include
from pygments.token import Generic, Name, Operator, Punctuation, Text, Whitespace


class ArgparseUsageLexer(RegexLexer):
    """Lexer for argparse usage lines only.

    Handles patterns like:
    - usage: PROG [-h] [--foo FOO] bar {a,b,c}
    - Mutually exclusive: [-a | -b], (--foo | --bar)
    - Choices: {json,yaml,table}
    - Variadic: FILE ..., [FILE ...], [--foo [FOO]]

    Examples
    --------
    >>> from pygments.token import Token
    >>> lexer = ArgparseUsageLexer()
    >>> tokens = list(lexer.get_tokens("usage: cmd [-h]"))
    >>> tokens[0]
    (Token.Generic.Heading, 'usage:')
    >>> tokens[2]
    (Token.Name.Label, 'cmd')
    """

    name = "Argparse Usage"
    aliases = ["argparse-usage"]  # noqa: RUF012
    filenames: list[str] = []  # noqa: RUF012
    mimetypes = ["text/x-argparse-usage"]  # noqa: RUF012

    tokens = {  # noqa: RUF012
        "root": [
            # "usage:" at start of line - then look for program name
            (
                r"^(usage:)(\s+)",
                bygroups(Generic.Heading, Whitespace),  # type: ignore[no-untyped-call]
                "after_usage",
            ),
            # Continuation lines (leading whitespace for wrapped usage)
            (r"^(\s+)(?=\S)", Whitespace),
            include("inline"),
        ],
        "after_usage": [
            # Whitespace
            (r"\s+", Whitespace),
            # Program name (first lowercase word after usage:)
            (r"\b[a-z][-a-z0-9]*\b", Name.Label, "usage_body"),
            # Fallback to inline if something unexpected
            include("inline"),
        ],
        "usage_body": [
            # Whitespace
            (r"\s+", Whitespace),
            # Ellipsis for variadic args (before other patterns)
            (r"\.\.\.", Punctuation),
            # Long options with = value (e.g., --log-level=VALUE)
            (
                r"(--[a-zA-Z0-9][-a-zA-Z0-9]*)(=)([A-Z][A-Z0-9_]*|[a-z][-a-z0-9]*)",
                bygroups(Name.Tag, Operator, Name.Variable),  # type: ignore[no-untyped-call]
            ),
            # Long options standalone
            (r"--[a-zA-Z0-9][-a-zA-Z0-9]*", Name.Tag),
            # Short options with space-separated value (e.g., -S socket-path)
            (
                r"(-[a-zA-Z0-9])(\s+)([A-Z][A-Z0-9_]*|[a-z][-a-z0-9]*)",
                bygroups(Name.Attribute, Whitespace, Name.Variable),  # type: ignore[no-untyped-call]
            ),
            # Short options standalone
            (r"-[a-zA-Z0-9]", Name.Attribute),
            # Opening brace - enter choices state
            (r"\{", Punctuation, "choices"),
            # Opening bracket - enter optional state
            (r"\[", Punctuation, "optional"),
            # Closing bracket (fallback for unmatched)
            (r"\]", Punctuation),
            # Opening paren - enter required mutex state
            (r"\(", Punctuation, "required"),
            # Closing paren (fallback for unmatched)
            (r"\)", Punctuation),
            # Choice separator (pipe) for mutex groups
            (r"\|", Operator),
            # UPPERCASE meta-variables (COMMAND, FILE, PATH)
            (r"\b[A-Z][A-Z0-9_]*\b", Name.Variable),
            # Subcommand/positional names (Name.Function for distinct styling)
            (r"\b[a-z][-a-z0-9]*\b", Name.Function),
            # Catch-all for any other text
            (r"[^\s\[\]|(){},]+", Text),
        ],
        "inline": [
            # Whitespace
            (r"\s+", Whitespace),
            # Ellipsis for variadic args (before other patterns)
            (r"\.\.\.", Punctuation),
            # Long options with = value (e.g., --log-level=VALUE)
            (
                r"(--[a-zA-Z0-9][-a-zA-Z0-9]*)(=)([A-Z][A-Z0-9_]*|[a-z][-a-z0-9]*)",
                bygroups(Name.Tag, Operator, Name.Variable),  # type: ignore[no-untyped-call]
            ),
            # Long options standalone
            (r"--[a-zA-Z0-9][-a-zA-Z0-9]*", Name.Tag),
            # Short options with space-separated value (e.g., -S socket-path)
            (
                r"(-[a-zA-Z0-9])(\s+)([A-Z][A-Z0-9_]*|[a-z][-a-z0-9]*)",
                bygroups(Name.Attribute, Whitespace, Name.Variable),  # type: ignore[no-untyped-call]
            ),
            # Short options standalone
            (r"-[a-zA-Z0-9]", Name.Attribute),
            # Opening brace - enter choices state
            (r"\{", Punctuation, "choices"),
            # Opening bracket - enter optional state
            (r"\[", Punctuation, "optional"),
            # Closing bracket (fallback for unmatched)
            (r"\]", Punctuation),
            # Opening paren - enter required mutex state
            (r"\(", Punctuation, "required"),
            # Closing paren (fallback for unmatched)
            (r"\)", Punctuation),
            # Choice separator (pipe) for mutex groups
            (r"\|", Operator),
            # UPPERCASE meta-variables (COMMAND, FILE, PATH)
            (r"\b[A-Z][A-Z0-9_]*\b", Name.Variable),
            # Positional/command names (lowercase with dashes)
            (r"\b[a-z][-a-z0-9]*\b", Name.Label),
            # Catch-all for any other text
            (r"[^\s\[\]|(){},]+", Text),
        ],
        "optional": [
            # Nested optional bracket
            (r"\[", Punctuation, "#push"),
            # End optional
            (r"\]", Punctuation, "#pop"),
            # Contents use usage_body rules (subcommands are green)
            include("usage_body"),
        ],
        "required": [
            # Nested required paren
            (r"\(", Punctuation, "#push"),
            # End required
            (r"\)", Punctuation, "#pop"),
            # Contents use usage_body rules (subcommands are green)
            include("usage_body"),
        ],
        "choices": [
            # Choice values (comma-separated inside braces)
            (r"[a-zA-Z0-9][-a-zA-Z0-9_]*", Name.Constant),
            # Comma separator
            (r",", Punctuation),
            # End choices
            (r"\}", Punctuation, "#pop"),
            # Whitespace
            (r"\s+", Whitespace),
        ],
    }


class ArgparseHelpLexer(RegexLexer):
    """Lexer for full argparse -h help output.

    Handles:
    - Usage lines (delegates to ArgparseUsageLexer patterns)
    - Section headers (positional arguments:, options:, etc.)
    - Option entries with help text
    - Indented descriptions

    Examples
    --------
    >>> from pygments.token import Token
    >>> lexer = ArgparseHelpLexer()
    >>> tokens = list(lexer.get_tokens("positional arguments:"))
    >>> any(t[0] == Token.Generic.Subheading for t in tokens)
    True
    >>> tokens = list(lexer.get_tokens("  -h, --help  show help"))
    >>> any(t[0] == Token.Name.Attribute for t in tokens)
    True
    """

    name = "Argparse Help"
    aliases = ["argparse-help"]  # noqa: RUF012
    filenames: list[str] = []  # noqa: RUF012
    mimetypes = ["text/x-argparse-help"]  # noqa: RUF012

    tokens = {  # noqa: RUF012
        "root": [
            # "usage:" line - switch to after_usage to find program name
            (
                r"^(usage:)(\s+)",
                bygroups(Generic.Heading, Whitespace),  # type: ignore[no-untyped-call]
                "after_usage",
            ),
            # Section headers (e.g., "positional arguments:", "options:")
            (r"^([a-zA-Z][-a-zA-Z0-9_ ]*:)\s*$", Generic.Subheading),
            # Option entry lines (indented with spaces/tabs, not just newlines)
            (r"^([ \t]+)", Whitespace, "option_line"),
            # Continuation of usage (leading spaces/tabs followed by content)
            (r"^([ \t]+)(?=\S)", Whitespace),
            # Anything else (must match at least one char to avoid infinite loop)
            (r".+\n?", Text),
            # Standalone newlines
            (r"\n", Whitespace),
        ],
        "after_usage": [
            # Whitespace
            (r"\s+", Whitespace),
            # Program name (first lowercase word after usage:)
            (r"\b[a-z][-a-z0-9]*\b", Name.Label, "usage"),
            # Fallback to usage if something unexpected
            include("usage_inline"),
        ],
        "usage": [
            # End of usage on blank line or section header
            (r"\n(?=[a-zA-Z][-a-zA-Z0-9_ ]*:\s*$)", Text, "#pop:2"),
            (r"\n(?=\n)", Text, "#pop:2"),
            # Usage content - use usage_inline rules (subcommands are green)
            include("usage_inline"),
            # Line continuation
            (r"\n", Text),
        ],
        "usage_inline": [
            # Whitespace
            (r"\s+", Whitespace),
            # Ellipsis for variadic args
            (r"\.\.\.", Punctuation),
            # Long options with = value
            (
                r"(--[a-zA-Z0-9][-a-zA-Z0-9]*)(=)([A-Z][A-Z0-9_]*|[a-z][-a-z0-9]*)",
                bygroups(Name.Tag, Operator, Name.Variable),  # type: ignore[no-untyped-call]
            ),
            # Long options standalone
            (r"--[a-zA-Z0-9][-a-zA-Z0-9]*", Name.Tag),
            # Short options with value
            (
                r"(-[a-zA-Z0-9])(\s+)([A-Z][A-Z0-9_]*|[a-z][-a-z0-9]*)",
                bygroups(Name.Attribute, Whitespace, Name.Variable),  # type: ignore[no-untyped-call]
            ),
            # Short options standalone
            (r"-[a-zA-Z0-9]", Name.Attribute),
            # Choices in braces
            (r"\{", Punctuation, "choices"),
            # Optional brackets
            (r"\[", Punctuation, "optional"),
            (r"\]", Punctuation),
            # Required parens (mutex)
            (r"\(", Punctuation, "required"),
            (r"\)", Punctuation),
            # Pipe for mutex
            (r"\|", Operator),
            # UPPERCASE metavars
            (r"\b[A-Z][A-Z0-9_]*\b", Name.Variable),
            # Subcommand/positional names (Name.Function for distinct styling)
            (r"\b[a-z][-a-z0-9]*\b", Name.Function),
            # Other text
            (r"[^\s\[\]|(){},\n]+", Text),
        ],
        "option_line": [
            # Short option with comma (e.g., "-h, --help")
            (
                r"(-[a-zA-Z0-9])(,)(\s*)(--[a-zA-Z0-9][-a-zA-Z0-9]*)",
                bygroups(Name.Attribute, Punctuation, Whitespace, Name.Tag),  # type: ignore[no-untyped-call]
            ),
            # Long options with = value
            (
                r"(--[a-zA-Z0-9][-a-zA-Z0-9]*)(=)([A-Z][A-Z0-9_]*|[a-z][-a-z0-9]*)",
                bygroups(Name.Tag, Operator, Name.Variable),  # type: ignore[no-untyped-call]
            ),
            # Long options with space-separated metavar
            (
                r"(--[a-zA-Z0-9][-a-zA-Z0-9]*)(\s+)([A-Z][A-Z0-9_]+)",
                bygroups(Name.Tag, Whitespace, Name.Variable),  # type: ignore[no-untyped-call]
            ),
            # Long options standalone
            (r"--[a-zA-Z0-9][-a-zA-Z0-9]*", Name.Tag),
            # Short options with metavar
            (
                r"(-[a-zA-Z0-9])(\s+)([A-Z][A-Z0-9_]+)",
                bygroups(Name.Attribute, Whitespace, Name.Variable),  # type: ignore[no-untyped-call]
            ),
            # Short options standalone
            (r"-[a-zA-Z0-9]", Name.Attribute),
            # Choices in braces
            (r"\{", Punctuation, "option_choices"),
            # Help text (everything after double space or large gap)
            (r"([ \t]{2,})(.+)$", bygroups(Whitespace, Text)),  # type: ignore[no-untyped-call]
            # End of line - MUST come before \s+ to properly pop on newlines
            (r"\n", Text, "#pop"),
            # Other whitespace (spaces/tabs only, not newlines)
            (r"[ \t]+", Whitespace),
            # UPPERCASE metavars
            (r"\b[A-Z][A-Z0-9_]*\b", Name.Variable),
            # Anything else on the line
            (r"[^\s\n]+", Text),
        ],
        "optional": [
            (r"\[", Punctuation, "#push"),
            (r"\]", Punctuation, "#pop"),
            include("usage_inline"),
        ],
        "required": [
            (r"\(", Punctuation, "#push"),
            (r"\)", Punctuation, "#pop"),
            include("usage_inline"),
        ],
        "choices": [
            (r"[a-zA-Z0-9][-a-zA-Z0-9_]*", Name.Constant),
            (r",", Punctuation),
            (r"\}", Punctuation, "#pop"),
            (r"\s+", Whitespace),
        ],
        "option_choices": [
            (r"[a-zA-Z0-9][-a-zA-Z0-9_]*", Name.Constant),
            (r",", Punctuation),
            (r"\}", Punctuation, "#pop"),
            (r"\s+", Whitespace),
        ],
    }


class ArgparseLexer(ArgparseHelpLexer):
    """Smart auto-detecting lexer for argparse output.

    Inherits from ArgparseHelpLexer to properly handle Pygments' metaclass
    token processing. Using inheritance (not token dict copying) avoids
    shared mutable state that causes memory corruption.

    This is the recommended lexer for general argparse highlighting.

    Examples
    --------
    >>> from pygments.token import Token
    >>> lexer = ArgparseLexer()

    Usage line detection:

    >>> tokens = list(lexer.get_tokens("usage: cmd [-h]"))
    >>> tokens[0]
    (Token.Generic.Heading, 'usage:')

    Section header detection (Pygments appends newline to input):

    >>> tokens = list(lexer.get_tokens("positional arguments:"))
    >>> any(t[0] == Token.Generic.Subheading for t in tokens)
    True

    Option highlighting in option line context:

    >>> tokens = list(lexer.get_tokens("  -h, --help  show help"))
    >>> any(t[0] == Token.Name.Attribute for t in tokens)
    True
    """

    name = "Argparse"
    aliases = ["argparse"]  # noqa: RUF012
    filenames: list[str] = []  # noqa: RUF012
    mimetypes = ["text/x-argparse"]  # noqa: RUF012

    # Tokens inherited from ArgparseHelpLexer - do NOT redefine or copy


def tokenize_argparse(text: str) -> list[tuple[str, str]]:
    """Tokenize argparse text and return list of (token_type, value) tuples.

    Parameters
    ----------
    text : str
        Argparse help or usage text to tokenize.

    Returns
    -------
    list[tuple[str, str]]
        List of (token_type_name, text_value) tuples.

    Examples
    --------
    >>> result = tokenize_argparse("usage: cmd [-h]")
    >>> result[0]
    ('Token.Generic.Heading', 'usage:')
    >>> result[2]
    ('Token.Name.Label', 'cmd')

    >>> result = tokenize_argparse("positional arguments:")
    >>> any('Token.Generic.Subheading' in t[0] for t in result)
    True
    """
    lexer = ArgparseLexer()
    return [
        (str(tok_type), tok_value) for tok_type, tok_value in lexer.get_tokens(text)
    ]


def tokenize_usage(text: str) -> list[tuple[str, str]]:
    """Tokenize usage text and return list of (token_type, value) tuples.

    Parameters
    ----------
    text : str
        CLI usage text to tokenize.

    Returns
    -------
    list[tuple[str, str]]
        List of (token_type_name, text_value) tuples.

    Examples
    --------
    >>> result = tokenize_usage("usage: cmd [-h]")
    >>> result[0]
    ('Token.Generic.Heading', 'usage:')
    >>> result[2]
    ('Token.Name.Label', 'cmd')
    >>> result[4]
    ('Token.Punctuation', '[')
    >>> result[5]
    ('Token.Name.Attribute', '-h')
    """
    lexer = ArgparseUsageLexer()
    return [
        (str(tok_type), tok_value) for tok_type, tok_value in lexer.get_tokens(text)
    ]
