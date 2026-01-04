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

import pathlib
import re
import typing as t

from tmuxp._internal.config_reader import ConfigReader
from tmuxp._internal.private_path import PrivatePath

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


class WorkspaceFields(t.TypedDict):
    """Extracted searchable fields from a workspace file.

    Attributes
    ----------
    name : str
        Workspace name (file stem without extension).
    path : str
        Path to workspace file (with ~ contraction).
    session_name : str
        Session name from config, or empty string if not found.
    windows : list[str]
        List of window names from config.
    panes : list[str]
        List of pane commands/shell_commands from config.

    Examples
    --------
    >>> fields: WorkspaceFields = {
    ...     "name": "dev",
    ...     "path": "~/.tmuxp/dev.yaml",
    ...     "session_name": "development",
    ...     "windows": ["editor", "shell"],
    ...     "panes": ["vim", "git status"],
    ... }
    >>> fields["name"]
    'dev'
    """

    name: str
    path: str
    session_name: str
    windows: list[str]
    panes: list[str]


class WorkspaceSearchResult(t.TypedDict):
    """Search result for a workspace that matched.

    Attributes
    ----------
    filepath : str
        Absolute path to the workspace file.
    source : str
        Source location: "local" or "global".
    fields : WorkspaceFields
        Extracted searchable fields.
    matches : dict[str, list[str]]
        Mapping of field name to matched strings for highlighting.

    Examples
    --------
    >>> result: WorkspaceSearchResult = {
    ...     "filepath": "/home/user/.tmuxp/dev.yaml",
    ...     "source": "global",
    ...     "fields": {
    ...         "name": "dev",
    ...         "path": "~/.tmuxp/dev.yaml",
    ...         "session_name": "development",
    ...         "windows": ["editor"],
    ...         "panes": [],
    ...     },
    ...     "matches": {"name": ["dev"]},
    ... }
    >>> result["source"]
    'global'
    """

    filepath: str
    source: str
    fields: WorkspaceFields
    matches: dict[str, list[str]]


def extract_workspace_fields(filepath: pathlib.Path) -> WorkspaceFields:
    """Extract searchable fields from a workspace file.

    Parses the workspace configuration and extracts name, path, session_name,
    window names, and pane commands for searching.

    Parameters
    ----------
    filepath : pathlib.Path
        Path to the workspace file.

    Returns
    -------
    WorkspaceFields
        Dictionary of extracted fields.

    Examples
    --------
    >>> import tempfile
    >>> import pathlib
    >>> content = '''
    ... session_name: my-project
    ... windows:
    ...   - window_name: editor
    ...     panes:
    ...       - vim
    ...       - shell_command: git status
    ...   - window_name: shell
    ... '''
    >>> with tempfile.NamedTemporaryFile(
    ...     suffix='.yaml', delete=False, mode='w'
    ... ) as f:
    ...     _ = f.write(content)
    ...     temp_path = pathlib.Path(f.name)
    >>> fields = extract_workspace_fields(temp_path)
    >>> fields["session_name"]
    'my-project'
    >>> sorted(fields["windows"])
    ['editor', 'shell']
    >>> 'vim' in fields["panes"]
    True
    >>> temp_path.unlink()
    """
    # Basic fields from file
    name = filepath.stem
    path = str(PrivatePath(filepath))

    # Try to parse config for session_name, windows, panes
    session_name = ""
    windows: list[str] = []
    panes: list[str] = []

    try:
        config = ConfigReader.from_file(filepath)
        if isinstance(config.content, dict):
            session_name = str(config.content.get("session_name", ""))

            # Extract window names and pane commands
            for window in config.content.get("windows", []):
                if not isinstance(window, dict):
                    continue

                # Window name
                if window_name := window.get("window_name"):
                    windows.append(str(window_name))

                # Pane commands
                for pane in window.get("panes", []):
                    if isinstance(pane, str):
                        panes.append(pane)
                    elif isinstance(pane, dict):
                        # shell_command can be str or list
                        cmds = pane.get("shell_command", [])
                        if isinstance(cmds, str):
                            panes.append(cmds)
                        elif isinstance(cmds, list):
                            panes.extend(str(cmd) for cmd in cmds if cmd)
    except Exception:
        # If config parsing fails, continue with empty content fields
        pass

    return WorkspaceFields(
        name=name,
        path=path,
        session_name=session_name,
        windows=windows,
        panes=panes,
    )


def _get_field_values(fields: WorkspaceFields, field_name: str) -> list[str]:
    """Get values for a field, normalizing to list.

    Parameters
    ----------
    fields : WorkspaceFields
        Extracted workspace fields.
    field_name : str
        Canonical field name to retrieve.

    Returns
    -------
    list[str]
        List of values for the field.

    Examples
    --------
    >>> fields: WorkspaceFields = {
    ...     "name": "dev",
    ...     "path": "~/.tmuxp/dev.yaml",
    ...     "session_name": "development",
    ...     "windows": ["editor", "shell"],
    ...     "panes": ["vim"],
    ... }
    >>> _get_field_values(fields, "name")
    ['dev']
    >>> _get_field_values(fields, "windows")
    ['editor', 'shell']
    >>> _get_field_values(fields, "window")
    ['editor', 'shell']
    """
    # Handle field name aliasing (window -> windows, pane -> panes)
    if field_name == "window":
        field_name = "windows"
    elif field_name == "pane":
        field_name = "panes"

    # Access fields directly for type safety
    if field_name == "name":
        return [fields["name"]] if fields["name"] else []
    if field_name == "path":
        return [fields["path"]] if fields["path"] else []
    if field_name == "session_name":
        return [fields["session_name"]] if fields["session_name"] else []
    if field_name == "windows":
        return fields["windows"]
    if field_name == "panes":
        return fields["panes"]

    return []


def evaluate_match(
    fields: WorkspaceFields,
    patterns: list[SearchPattern],
    *,
    match_any: bool = False,
) -> tuple[bool, dict[str, list[str]]]:
    """Evaluate if workspace fields match search patterns.

    Parameters
    ----------
    fields : WorkspaceFields
        Extracted workspace fields to search.
    patterns : list[SearchPattern]
        Compiled search patterns.
    match_any : bool
        If True, match if ANY pattern matches (OR logic).
        If False, ALL patterns must match (AND logic). Default False.

    Returns
    -------
    tuple[bool, dict[str, list[str]]]
        Tuple of (matched, {field_name: [matched_strings]}).
        The matches dict contains actual matched text for highlighting.

    Examples
    --------
    >>> import re
    >>> fields: WorkspaceFields = {
    ...     "name": "dev-project",
    ...     "path": "~/.tmuxp/dev-project.yaml",
    ...     "session_name": "development",
    ...     "windows": ["editor", "shell"],
    ...     "panes": ["vim", "git status"],
    ... }

    Single pattern match:

    >>> pattern = SearchPattern(
    ...     fields=("name",),
    ...     raw="dev",
    ...     regex=re.compile("dev"),
    ... )
    >>> matched, matches = evaluate_match(fields, [pattern])
    >>> matched
    True
    >>> "name" in matches
    True

    AND logic (default) - all patterns must match:

    >>> p1 = SearchPattern(fields=("name",), raw="dev", regex=re.compile("dev"))
    >>> p2 = SearchPattern(fields=("name",), raw="xyz", regex=re.compile("xyz"))
    >>> matched, _ = evaluate_match(fields, [p1, p2], match_any=False)
    >>> matched
    False

    OR logic - any pattern can match:

    >>> matched, _ = evaluate_match(fields, [p1, p2], match_any=True)
    >>> matched
    True

    Window field search:

    >>> p_win = SearchPattern(
    ...     fields=("window",),
    ...     raw="editor",
    ...     regex=re.compile("editor"),
    ... )
    >>> matched, matches = evaluate_match(fields, [p_win])
    >>> matched
    True
    >>> "window" in matches
    True
    """
    all_matches: dict[str, list[str]] = {}
    pattern_results: list[bool] = []

    for pattern in patterns:
        pattern_matched = False

        for field_name in pattern.fields:
            values = _get_field_values(fields, field_name)

            for value in values:
                if match := pattern.regex.search(value):
                    pattern_matched = True
                    # Store matched text for highlighting
                    if field_name not in all_matches:
                        all_matches[field_name] = []
                    all_matches[field_name].append(match.group())

        pattern_results.append(pattern_matched)

    # Apply match logic
    if match_any:
        final_matched = any(pattern_results)
    else:
        final_matched = all(pattern_results) if pattern_results else False

    return final_matched, all_matches


def find_search_matches(
    workspaces: list[tuple[pathlib.Path, str]],
    patterns: list[SearchPattern],
    *,
    match_any: bool = False,
    invert_match: bool = False,
) -> list[WorkspaceSearchResult]:
    """Find workspaces matching search patterns.

    Parameters
    ----------
    workspaces : list[tuple[pathlib.Path, str]]
        List of (filepath, source) tuples to search. Source is "local" or "global".
    patterns : list[SearchPattern]
        Compiled search patterns.
    match_any : bool
        If True, match if ANY pattern matches (OR logic). Default False (AND).
    invert_match : bool
        If True, return workspaces that do NOT match. Default False.

    Returns
    -------
    list[WorkspaceSearchResult]
        List of matching workspace results with match information.

    Examples
    --------
    >>> import tempfile
    >>> import pathlib
    >>> import re
    >>> content = "session_name: dev-session" + chr(10) + "windows: []"
    >>> with tempfile.NamedTemporaryFile(
    ...     suffix='.yaml', delete=False, mode='w'
    ... ) as f:
    ...     _ = f.write(content)
    ...     temp_path = pathlib.Path(f.name)

    >>> pattern = SearchPattern(
    ...     fields=("session_name",),
    ...     raw="dev",
    ...     regex=re.compile("dev"),
    ... )
    >>> results = find_search_matches([(temp_path, "global")], [pattern])
    >>> len(results)
    1
    >>> results[0]["source"]
    'global'

    Invert match returns non-matching workspaces:

    >>> pattern_nomatch = SearchPattern(
    ...     fields=("name",),
    ...     raw="nonexistent",
    ...     regex=re.compile("nonexistent"),
    ... )
    >>> results = find_search_matches(
    ...     [(temp_path, "global")], [pattern_nomatch], invert_match=True
    ... )
    >>> len(results)
    1
    >>> temp_path.unlink()
    """
    results: list[WorkspaceSearchResult] = []

    for filepath, source in workspaces:
        fields = extract_workspace_fields(filepath)
        matched, matches = evaluate_match(fields, patterns, match_any=match_any)

        # Apply invert logic
        if invert_match:
            matched = not matched

        if matched:
            results.append(
                WorkspaceSearchResult(
                    filepath=str(filepath),
                    source=source,
                    fields=fields,
                    matches=matches,
                )
            )

    return results
