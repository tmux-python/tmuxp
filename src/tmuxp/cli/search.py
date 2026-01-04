"""CLI for ``tmuxp search`` subcommand.

Search workspace configuration files by name, session, path, and content.

Examples
--------
>>> from tmuxp.cli.search import SearchToken, normalize_fields

Parse field aliases to canonical names:

>>> normalize_fields(["s", "name"])
('session_name', 'name')

Create search tokens from query terms:

>>> from tmuxp.cli.search import parse_query_terms, DEFAULT_FIELDS
>>> tokens = parse_query_terms(["name:dev", "editor"], default_fields=DEFAULT_FIELDS)
>>> tokens[0]
SearchToken(fields=('name',), pattern='dev')
>>> tokens[1]
SearchToken(fields=('name', 'session_name', 'path'), pattern='editor')
"""

from __future__ import annotations

import re
import typing as t

if t.TYPE_CHECKING:
    pass

#: Field name aliases for search queries
FIELD_ALIASES: dict[str, str] = {
    "name": "name",
    "n": "name",
    "session": "session_name",
    "session_name": "session_name",
    "s": "session_name",
    "path": "path",
    "p": "path",
    "window": "window",
    "w": "window",
    "pane": "pane",
}

#: Valid field names after alias resolution
VALID_FIELDS: frozenset[str] = frozenset(
    {"name", "session_name", "path", "window", "pane"}
)

#: Default fields to search when no field prefix is specified
DEFAULT_FIELDS: tuple[str, ...] = ("name", "session_name", "path")


class SearchToken(t.NamedTuple):
    """Parsed search token with target fields and raw pattern.

    Attributes
    ----------
    fields : tuple[str, ...]
        Canonical field names to search (e.g., ('name', 'session_name')).
    pattern : str
        Raw search pattern before regex compilation.

    Examples
    --------
    >>> token = SearchToken(fields=("name",), pattern="dev")
    >>> token.fields
    ('name',)
    >>> token.pattern
    'dev'
    """

    fields: tuple[str, ...]
    pattern: str


class SearchPattern(t.NamedTuple):
    """Compiled search pattern with regex and metadata.

    Attributes
    ----------
    fields : tuple[str, ...]
        Canonical field names to search.
    raw : str
        Original pattern string before compilation.
    regex : re.Pattern[str]
        Compiled regex pattern for matching.

    Examples
    --------
    >>> import re
    >>> pattern = SearchPattern(
    ...     fields=("name",),
    ...     raw="dev",
    ...     regex=re.compile("dev"),
    ... )
    >>> pattern.fields
    ('name',)
    >>> bool(pattern.regex.search("development"))
    True
    """

    fields: tuple[str, ...]
    raw: str
    regex: re.Pattern[str]


class InvalidFieldError(ValueError):
    """Raised when an invalid field name is specified.

    Examples
    --------
    >>> raise InvalidFieldError("invalid")
    Traceback (most recent call last):
        ...
    tmuxp.cli.search.InvalidFieldError: Unknown search field: 'invalid'. ...
    """

    def __init__(self, field: str) -> None:
        valid = ", ".join(sorted(FIELD_ALIASES.keys()))
        super().__init__(f"Unknown search field: '{field}'. Valid fields: {valid}")
        self.field = field


def normalize_fields(fields: list[str] | None) -> tuple[str, ...]:
    """Normalize field names using aliases.

    Parameters
    ----------
    fields : list[str] | None
        Field names or aliases to normalize. If None, returns DEFAULT_FIELDS.

    Returns
    -------
    tuple[str, ...]
        Tuple of canonical field names.

    Raises
    ------
    InvalidFieldError
        If a field name is not recognized.

    Examples
    --------
    >>> normalize_fields(None)
    ('name', 'session_name', 'path')

    >>> normalize_fields(["s", "n"])
    ('session_name', 'name')

    >>> normalize_fields(["session_name", "path"])
    ('session_name', 'path')

    >>> normalize_fields(["invalid"])
    Traceback (most recent call last):
        ...
    tmuxp.cli.search.InvalidFieldError: Unknown search field: 'invalid'. ...
    """
    if fields is None:
        return DEFAULT_FIELDS

    result: list[str] = []
    for field in fields:
        field_lower = field.lower()
        if field_lower not in FIELD_ALIASES:
            raise InvalidFieldError(field)
        canonical = FIELD_ALIASES[field_lower]
        if canonical not in result:
            result.append(canonical)

    return tuple(result)


def _parse_field_prefix(term: str) -> tuple[str | None, str]:
    """Extract field prefix from a search term.

    Parameters
    ----------
    term : str
        Search term, possibly with field prefix (e.g., "name:dev").

    Returns
    -------
    tuple[str | None, str]
        Tuple of (field_prefix, pattern). field_prefix is None if no prefix.

    Examples
    --------
    >>> _parse_field_prefix("name:dev")
    ('name', 'dev')

    >>> _parse_field_prefix("s:myproject")
    ('s', 'myproject')

    >>> _parse_field_prefix("development")
    (None, 'development')

    >>> _parse_field_prefix("path:/home/user")
    ('path', '/home/user')

    >>> _parse_field_prefix("window:")
    ('window', '')
    """
    if ":" not in term:
        return None, term

    # Split on first colon only
    prefix, _, pattern = term.partition(":")
    prefix_lower = prefix.lower()

    # Check if prefix is a valid field alias
    if prefix_lower in FIELD_ALIASES:
        return prefix, pattern

    # Not a valid field prefix, treat entire term as pattern
    return None, term


def parse_query_terms(
    terms: list[str],
    *,
    default_fields: tuple[str, ...] = DEFAULT_FIELDS,
) -> list[SearchToken]:
    """Parse query terms into search tokens.

    Each term can optionally have a field prefix (e.g., "name:dev").
    Terms without prefixes search the default fields.

    Parameters
    ----------
    terms : list[str]
        Query terms to parse.
    default_fields : tuple[str, ...]
        Fields to search when no prefix is specified.

    Returns
    -------
    list[SearchToken]
        List of parsed search tokens.

    Raises
    ------
    InvalidFieldError
        If a field prefix is not recognized.

    Examples
    --------
    >>> tokens = parse_query_terms(["dev"])
    >>> tokens[0].fields
    ('name', 'session_name', 'path')
    >>> tokens[0].pattern
    'dev'

    >>> tokens = parse_query_terms(["name:dev", "s:prod"])
    >>> tokens[0]
    SearchToken(fields=('name',), pattern='dev')
    >>> tokens[1]
    SearchToken(fields=('session_name',), pattern='prod')

    >>> tokens = parse_query_terms(["window:editor", "shell"])
    >>> tokens[0].fields
    ('window',)
    >>> tokens[1].fields
    ('name', 'session_name', 'path')

    Unknown prefixes are treated as literal patterns (allows URLs, etc.):

    >>> tokens = parse_query_terms(["http://example.com"])
    >>> tokens[0].pattern
    'http://example.com'
    >>> tokens[0].fields  # Searches default fields
    ('name', 'session_name', 'path')
    """
    result: list[SearchToken] = []

    for term in terms:
        if not term:
            continue

        prefix, pattern = _parse_field_prefix(term)

        # Validate and resolve field prefix, or use defaults
        fields = normalize_fields([prefix]) if prefix is not None else default_fields

        if pattern:  # Skip empty patterns
            result.append(SearchToken(fields=fields, pattern=pattern))

    return result


def _has_uppercase(pattern: str) -> bool:
    """Check if pattern contains uppercase letters.

    Used for smart-case detection.

    Parameters
    ----------
    pattern : str
        Pattern to check.

    Returns
    -------
    bool
        True if pattern contains at least one uppercase letter.

    Examples
    --------
    >>> _has_uppercase("dev")
    False

    >>> _has_uppercase("Dev")
    True

    >>> _has_uppercase("DEV")
    True

    >>> _has_uppercase("123")
    False

    >>> _has_uppercase("")
    False
    """
    return any(c.isupper() for c in pattern)


def compile_search_patterns(
    tokens: list[SearchToken],
    *,
    ignore_case: bool = False,
    smart_case: bool = False,
    fixed_strings: bool = False,
    word_regexp: bool = False,
) -> list[SearchPattern]:
    """Compile search tokens into regex patterns.

    Parameters
    ----------
    tokens : list[SearchToken]
        Parsed search tokens to compile.
    ignore_case : bool
        If True, always ignore case. Default False.
    smart_case : bool
        If True, ignore case unless pattern has uppercase. Default False.
    fixed_strings : bool
        If True, treat patterns as literal strings, not regex. Default False.
    word_regexp : bool
        If True, match whole words only. Default False.

    Returns
    -------
    list[SearchPattern]
        List of compiled search patterns.

    Raises
    ------
    re.error
        If a pattern is invalid regex (when fixed_strings=False).

    Examples
    --------
    Basic compilation:

    >>> tokens = [SearchToken(fields=("name",), pattern="dev")]
    >>> patterns = compile_search_patterns(tokens)
    >>> patterns[0].raw
    'dev'
    >>> bool(patterns[0].regex.search("development"))
    True

    Case-insensitive matching:

    >>> tokens = [SearchToken(fields=("name",), pattern="DEV")]
    >>> patterns = compile_search_patterns(tokens, ignore_case=True)
    >>> bool(patterns[0].regex.search("development"))
    True

    Smart-case (uppercase = case-sensitive):

    >>> tokens = [SearchToken(fields=("name",), pattern="Dev")]
    >>> patterns = compile_search_patterns(tokens, smart_case=True)
    >>> bool(patterns[0].regex.search("Developer"))
    True
    >>> bool(patterns[0].regex.search("developer"))
    False

    Smart-case (lowercase = case-insensitive):

    >>> tokens = [SearchToken(fields=("name",), pattern="dev")]
    >>> patterns = compile_search_patterns(tokens, smart_case=True)
    >>> bool(patterns[0].regex.search("DEVELOPMENT"))
    True

    Fixed strings (escape regex metacharacters):

    >>> tokens = [SearchToken(fields=("name",), pattern="dev.*")]
    >>> patterns = compile_search_patterns(tokens, fixed_strings=True)
    >>> bool(patterns[0].regex.search("dev.*project"))
    True
    >>> bool(patterns[0].regex.search("development"))
    False

    Word boundaries:

    >>> tokens = [SearchToken(fields=("name",), pattern="dev")]
    >>> patterns = compile_search_patterns(tokens, word_regexp=True)
    >>> bool(patterns[0].regex.search("my dev project"))
    True
    >>> bool(patterns[0].regex.search("development"))
    False
    """
    result: list[SearchPattern] = []

    for token in tokens:
        pattern_str = token.pattern

        # Escape for literal matching if requested
        if fixed_strings:
            pattern_str = re.escape(pattern_str)

        # Add word boundaries if requested
        if word_regexp:
            pattern_str = rf"\b{pattern_str}\b"

        # Determine case sensitivity
        flags = 0
        if ignore_case or (smart_case and not _has_uppercase(token.pattern)):
            flags |= re.IGNORECASE

        compiled = re.compile(pattern_str, flags)
        result.append(
            SearchPattern(
                fields=token.fields,
                raw=token.pattern,
                regex=compiled,
            )
        )

    return result
