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
SearchToken(fields=('name', 'session_name', 'path', 'window', 'pane'), pattern='editor')
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import typing as t

import yaml

from tmuxp._internal.config_reader import ConfigReader
from tmuxp._internal.private_path import PrivatePath
from tmuxp.workspace.constants import VALID_WORKSPACE_DIR_FILE_EXTENSIONS
from tmuxp.workspace.finders import find_local_workspace_files, get_workspace_dir

from ._colors import Colors, build_description, get_color_mode
from ._output import OutputFormatter, get_output_mode

if t.TYPE_CHECKING:
    from typing import TypeAlias

    CLIColorModeLiteral: TypeAlias = t.Literal["auto", "always", "never"]

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
DEFAULT_FIELDS: tuple[str, ...] = ("name", "session_name", "path", "window", "pane")


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
    >>> raise InvalidFieldError("invalid")  # doctest: +ELLIPSIS
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
    ('name', 'session_name', 'path', 'window', 'pane')

    >>> normalize_fields(["s", "n"])
    ('session_name', 'name')

    >>> normalize_fields(["session_name", "path"])
    ('session_name', 'path')

    >>> normalize_fields(["invalid"])  # doctest: +ELLIPSIS
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
    ('name', 'session_name', 'path', 'window', 'pane')
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
    ('name', 'session_name', 'path', 'window', 'pane')

    Unknown prefixes are treated as literal patterns (allows URLs, etc.):

    >>> tokens = parse_query_terms(["http://example.com"])
    >>> tokens[0].pattern
    'http://example.com'
    >>> tokens[0].fields  # Searches default fields
    ('name', 'session_name', 'path', 'window', 'pane')
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
    except (yaml.YAMLError, json.JSONDecodeError, OSError):
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


def highlight_matches(
    text: str,
    patterns: list[SearchPattern],
    *,
    colors: Colors,
) -> str:
    """Highlight regex matches in text.

    Parameters
    ----------
    text : str
        Text to search and highlight.
    patterns : list[SearchPattern]
        Compiled search patterns (uses their regex attribute).
    colors : Colors
        Color manager for highlighting.

    Returns
    -------
    str
        Text with matches highlighted, or original text if no matches.

    Examples
    --------
    >>> from tmuxp.cli._colors import ColorMode, Colors
    >>> colors = Colors(ColorMode.NEVER)
    >>> pattern = SearchPattern(
    ...     fields=("name",),
    ...     raw="dev",
    ...     regex=re.compile("dev"),
    ... )
    >>> highlight_matches("development", [pattern], colors=colors)
    'development'

    With colors enabled (ALWAYS mode):

    >>> colors_on = Colors(ColorMode.ALWAYS)
    >>> result = highlight_matches("development", [pattern], colors=colors_on)
    >>> "dev" in result
    True
    >>> chr(27) in result  # Contains ANSI escape
    True
    """
    if not patterns:
        return text

    # Collect all match spans
    spans: list[tuple[int, int]] = []
    for pattern in patterns:
        spans.extend((m.start(), m.end()) for m in pattern.regex.finditer(text))

    if not spans:
        return text

    # Sort and merge overlapping spans
    spans.sort()
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            # Overlapping or adjacent, extend previous
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Build result with highlights
    result: list[str] = []
    pos = 0
    for start, end in merged:
        # Add non-matching text before this match
        if pos < start:
            result.append(text[pos:start])
        # Add highlighted match
        result.append(colors.highlight(text[start:end]))
        pos = end

    # Add any remaining text after last match
    if pos < len(text):
        result.append(text[pos:])

    return "".join(result)


def _output_search_results(
    results: list[WorkspaceSearchResult],
    patterns: list[SearchPattern],
    formatter: OutputFormatter,
    colors: Colors,
) -> None:
    """Output search results in human-readable or JSON format.

    Parameters
    ----------
    results : list[WorkspaceSearchResult]
        Search results to output.
    patterns : list[SearchPattern]
        Patterns used for highlighting.
    formatter : OutputFormatter
        Output formatter for JSON/NDJSON/human modes.
    colors : Colors
        Color manager.
    """
    if not results:
        formatter.emit_text(colors.warning("No matching workspaces found."))
        return

    # Group by source for human output
    local_results = [r for r in results if r["source"] == "local"]
    global_results = [r for r in results if r["source"] == "global"]

    def output_result(result: WorkspaceSearchResult, show_path: bool) -> None:
        """Output a single search result."""
        fields = result["fields"]

        # JSON/NDJSON output: emit structured data
        json_data = {
            "name": fields["name"],
            "path": fields["path"],
            "session_name": fields["session_name"],
            "source": result["source"],
            "matched_fields": list(result["matches"].keys()),
            "matches": result["matches"],
        }
        formatter.emit(json_data)

        # Human output: formatted text with highlighting
        name_display = highlight_matches(fields["name"], patterns, colors=colors)
        path_info = f"  {colors.info(fields['path'])}" if show_path else ""
        formatter.emit_text(f"  {colors.highlight(name_display)}{path_info}")

        # Show matched session_name if different from name
        session_name = fields["session_name"]
        if session_name and session_name != fields["name"]:
            session_display = highlight_matches(session_name, patterns, colors=colors)
            formatter.emit_text(f"    session: {session_display}")

        # Show matched windows
        if result["matches"].get("window"):
            window_names = [
                highlight_matches(w, patterns, colors=colors) for w in fields["windows"]
            ]
            if window_names:
                formatter.emit_text(f"    windows: {', '.join(window_names)}")

        # Show matched panes
        if result["matches"].get("pane"):
            pane_cmds = fields["panes"][:3]  # Limit to first 3
            pane_displays = [
                highlight_matches(p, patterns, colors=colors) for p in pane_cmds
            ]
            if len(fields["panes"]) > 3:
                pane_displays.append("...")
            if pane_displays:
                formatter.emit_text(f"    panes: {', '.join(pane_displays)}")

    # Output local results first
    if local_results:
        formatter.emit_text(colors.heading("Local workspaces:"))
        for result in local_results:
            output_result(result, show_path=True)

    # Output global results
    if global_results:
        if local_results:
            formatter.emit_text("")  # Blank line separator
        formatter.emit_text(colors.heading("Global workspaces:"))
        for result in global_results:
            output_result(result, show_path=False)


SEARCH_DESCRIPTION = build_description(
    """
    Search workspace files by name, session, path, window, or pane content.
    """,
    (
        (
            None,
            [
                "tmuxp search dev",
                'tmuxp search "my.*project"',
                "tmuxp search name:dev",
                "tmuxp search s:development",
            ],
        ),
        (
            "Field-scoped search",
            [
                "tmuxp search window:editor",
                "tmuxp search pane:vim",
                "tmuxp search p:~/.tmuxp",
            ],
        ),
        (
            "Matching options",
            [
                "tmuxp search -i DEV",
                "tmuxp search -S DevProject",
                "tmuxp search -F 'my.project'",
                "tmuxp search --word-regexp test",
            ],
        ),
        (
            "Multiple patterns",
            [
                "tmuxp search dev production",
                "tmuxp search --any dev production",
                "tmuxp search -v staging",
            ],
        ),
        (
            "Machine-readable output examples",
            [
                "tmuxp search --json dev",
                "tmuxp search --ndjson dev | jq '.name'",
            ],
        ),
    ),
)


class CLISearchNamespace(argparse.Namespace):
    """Typed :class:`argparse.Namespace` for tmuxp search command.

    Examples
    --------
    >>> ns = CLISearchNamespace()
    >>> ns.query_terms = ["dev"]
    >>> ns.query_terms
    ['dev']
    """

    color: CLIColorModeLiteral
    query_terms: list[str]
    field: list[str] | None
    ignore_case: bool
    smart_case: bool
    fixed_strings: bool
    word_regexp: bool
    invert_match: bool
    match_any: bool
    output_json: bool
    output_ndjson: bool
    print_help: t.Callable[[], None]


def create_search_subparser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Augment :class:`argparse.ArgumentParser` with ``search`` subcommand.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser to augment.

    Returns
    -------
    argparse.ArgumentParser
        The augmented parser.

    Examples
    --------
    >>> import argparse
    >>> parser = argparse.ArgumentParser()
    >>> result = create_search_subparser(parser)
    >>> result is parser
    True
    """
    # Positional arguments
    parser.add_argument(
        "query_terms",
        nargs="*",
        metavar="PATTERN",
        help="search patterns (prefix with field: for field-scoped search)",
    )

    # Field restriction
    parser.add_argument(
        "-f",
        "--field",
        action="append",
        metavar="FIELD",
        help="restrict search to field(s): name, session/s, path/p, window/w, pane",
    )

    # Matching options
    parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="case-insensitive matching",
    )
    parser.add_argument(
        "-S",
        "--smart-case",
        action="store_true",
        help="case-insensitive unless pattern has uppercase",
    )
    parser.add_argument(
        "-F",
        "--fixed-strings",
        action="store_true",
        help="treat patterns as literal strings, not regex",
    )
    parser.add_argument(
        "-w",
        "--word-regexp",
        action="store_true",
        help="match whole words only",
    )
    parser.add_argument(
        "-v",
        "--invert-match",
        action="store_true",
        help="show workspaces that do NOT match",
    )
    parser.add_argument(
        "--any",
        dest="match_any",
        action="store_true",
        help="match ANY pattern (OR logic); default is ALL (AND logic)",
    )

    # Output format
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="output as JSON",
    )
    parser.add_argument(
        "--ndjson",
        action="store_true",
        dest="output_ndjson",
        help="output as NDJSON (one JSON per line)",
    )

    # Store print_help for use when no arguments provided
    parser.set_defaults(print_help=parser.print_help)

    return parser


def command_search(
    args: CLISearchNamespace | None = None,
    parser: argparse.ArgumentParser | None = None,
) -> None:
    """Entrypoint for ``tmuxp search`` subcommand.

    Searches workspace files in local (cwd and parents) and global (~/.tmuxp/)
    directories.

    Parameters
    ----------
    args : CLISearchNamespace | None
        Parsed command-line arguments.
    parser : argparse.ArgumentParser | None
        The argument parser (unused but required by CLI interface).

    Examples
    --------
    >>> # command_search() searches workspaces with given patterns
    """
    # Get color mode from args or default to AUTO
    color_mode = get_color_mode(args.color if args else None)
    colors = Colors(color_mode)

    # Determine output mode
    output_json = args.output_json if args else False
    output_ndjson = args.output_ndjson if args else False
    output_mode = get_output_mode(output_json, output_ndjson)
    formatter = OutputFormatter(output_mode)

    # Get query terms
    query_terms = args.query_terms if args else []

    if not query_terms:
        if args and hasattr(args, "print_help"):
            args.print_help()
        return

    # Parse and compile patterns
    try:
        # Get default fields (possibly restricted by --field)
        default_fields = normalize_fields(args.field if args else None)
        tokens = parse_query_terms(query_terms, default_fields=default_fields)

        if not tokens:
            formatter.emit_text(colors.warning("No valid search patterns."))
            formatter.finalize()
            return

        patterns = compile_search_patterns(
            tokens,
            ignore_case=args.ignore_case if args else False,
            smart_case=args.smart_case if args else False,
            fixed_strings=args.fixed_strings if args else False,
            word_regexp=args.word_regexp if args else False,
        )
    except InvalidFieldError as e:
        formatter.emit_text(colors.error(str(e)))
        formatter.finalize()
        return
    except re.error as e:
        formatter.emit_text(colors.error(f"Invalid regex pattern: {e}"))
        formatter.finalize()
        return

    # Collect workspaces: local (cwd + parents) + global (~/.tmuxp/)
    workspaces: list[tuple[pathlib.Path, str]] = []

    # Local workspace files
    local_files = find_local_workspace_files()
    workspaces.extend((f, "local") for f in local_files)

    # Global workspace files
    tmuxp_dir = pathlib.Path(get_workspace_dir())
    if tmuxp_dir.exists() and tmuxp_dir.is_dir():
        workspaces.extend(
            (f, "global")
            for f in sorted(tmuxp_dir.iterdir())
            if not f.is_dir()
            and f.suffix.lower() in VALID_WORKSPACE_DIR_FILE_EXTENSIONS
        )

    if not workspaces:
        formatter.emit_text(colors.warning("No workspaces found."))
        formatter.finalize()
        return

    # Find matches
    results = find_search_matches(
        workspaces,
        patterns,
        match_any=args.match_any if args else False,
        invert_match=args.invert_match if args else False,
    )

    # Output results
    _output_search_results(results, patterns, formatter, colors)
    formatter.finalize()
