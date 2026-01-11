"""CLI tests for tmuxp search command."""

from __future__ import annotations

import json
import pathlib
import re
import typing as t

import pytest

from tmuxp.cli._colors import ColorMode, Colors
from tmuxp.cli._output import OutputFormatter, OutputMode
from tmuxp.cli.search import (
    DEFAULT_FIELDS,
    InvalidFieldError,
    SearchPattern,
    SearchToken,
    WorkspaceFields,
    WorkspaceSearchResult,
    _get_field_values,
    _output_search_results,
    compile_search_patterns,
    create_search_subparser,
    evaluate_match,
    extract_workspace_fields,
    find_search_matches,
    highlight_matches,
    normalize_fields,
    parse_query_terms,
)


class NormalizeFieldsFixture(t.NamedTuple):
    """Test fixture for normalize_fields."""

    test_id: str
    fields: list[str] | None
    expected: tuple[str, ...]
    raises: type[Exception] | None


NORMALIZE_FIELDS_FIXTURES: list[NormalizeFieldsFixture] = [
    NormalizeFieldsFixture(
        test_id="none_returns_defaults",
        fields=None,
        expected=DEFAULT_FIELDS,
        raises=None,
    ),
    NormalizeFieldsFixture(
        test_id="name_alias",
        fields=["n"],
        expected=("name",),
        raises=None,
    ),
    NormalizeFieldsFixture(
        test_id="session_aliases",
        fields=["s", "session", "session_name"],
        expected=("session_name",),
        raises=None,
    ),
    NormalizeFieldsFixture(
        test_id="path_alias",
        fields=["p"],
        expected=("path",),
        raises=None,
    ),
    NormalizeFieldsFixture(
        test_id="window_alias",
        fields=["w"],
        expected=("window",),
        raises=None,
    ),
    NormalizeFieldsFixture(
        test_id="multiple_fields",
        fields=["name", "s", "window"],
        expected=("name", "session_name", "window"),
        raises=None,
    ),
    NormalizeFieldsFixture(
        test_id="invalid_field",
        fields=["invalid"],
        expected=(),
        raises=InvalidFieldError,
    ),
    NormalizeFieldsFixture(
        test_id="case_insensitive",
        fields=["NAME", "Session"],
        expected=("name", "session_name"),
        raises=None,
    ),
]


@pytest.mark.parametrize(
    NormalizeFieldsFixture._fields,
    NORMALIZE_FIELDS_FIXTURES,
    ids=[test.test_id for test in NORMALIZE_FIELDS_FIXTURES],
)
def test_normalize_fields(
    test_id: str,
    fields: list[str] | None,
    expected: tuple[str, ...],
    raises: type[Exception] | None,
) -> None:
    """Test normalize_fields function."""
    if raises:
        with pytest.raises(raises):
            normalize_fields(fields)
    else:
        result = normalize_fields(fields)
        assert result == expected


class ParseQueryTermsFixture(t.NamedTuple):
    """Test fixture for parse_query_terms."""

    test_id: str
    terms: list[str]
    expected_count: int
    expected_first_fields: tuple[str, ...] | None
    expected_first_pattern: str | None


PARSE_QUERY_TERMS_FIXTURES: list[ParseQueryTermsFixture] = [
    ParseQueryTermsFixture(
        test_id="simple_term",
        terms=["dev"],
        expected_count=1,
        expected_first_fields=DEFAULT_FIELDS,
        expected_first_pattern="dev",
    ),
    ParseQueryTermsFixture(
        test_id="name_prefix",
        terms=["name:dev"],
        expected_count=1,
        expected_first_fields=("name",),
        expected_first_pattern="dev",
    ),
    ParseQueryTermsFixture(
        test_id="session_prefix",
        terms=["s:production"],
        expected_count=1,
        expected_first_fields=("session_name",),
        expected_first_pattern="production",
    ),
    ParseQueryTermsFixture(
        test_id="multiple_terms",
        terms=["dev", "production"],
        expected_count=2,
        expected_first_fields=DEFAULT_FIELDS,
        expected_first_pattern="dev",
    ),
    ParseQueryTermsFixture(
        test_id="url_not_field",
        terms=["http://example.com"],
        expected_count=1,
        expected_first_fields=DEFAULT_FIELDS,
        expected_first_pattern="http://example.com",
    ),
    ParseQueryTermsFixture(
        test_id="empty_pattern_skipped",
        terms=["name:"],
        expected_count=0,
        expected_first_fields=None,
        expected_first_pattern=None,
    ),
    ParseQueryTermsFixture(
        test_id="path_with_colons",
        terms=["path:/home/user/project"],
        expected_count=1,
        expected_first_fields=("path",),
        expected_first_pattern="/home/user/project",
    ),
]


@pytest.mark.parametrize(
    ParseQueryTermsFixture._fields,
    PARSE_QUERY_TERMS_FIXTURES,
    ids=[test.test_id for test in PARSE_QUERY_TERMS_FIXTURES],
)
def test_parse_query_terms(
    test_id: str,
    terms: list[str],
    expected_count: int,
    expected_first_fields: tuple[str, ...] | None,
    expected_first_pattern: str | None,
) -> None:
    """Test parse_query_terms function."""
    result = parse_query_terms(terms)

    assert len(result) == expected_count

    if expected_count > 0:
        assert result[0].fields == expected_first_fields
        assert result[0].pattern == expected_first_pattern


class CompileSearchPatternsFixture(t.NamedTuple):
    """Test fixture for compile_search_patterns."""

    test_id: str
    pattern: str
    ignore_case: bool
    smart_case: bool
    fixed_strings: bool
    word_regexp: bool
    test_string: str
    should_match: bool


COMPILE_SEARCH_PATTERNS_FIXTURES: list[CompileSearchPatternsFixture] = [
    CompileSearchPatternsFixture(
        test_id="basic_match",
        pattern="dev",
        ignore_case=False,
        smart_case=False,
        fixed_strings=False,
        word_regexp=False,
        test_string="development",
        should_match=True,
    ),
    CompileSearchPatternsFixture(
        test_id="case_sensitive_no_match",
        pattern="DEV",
        ignore_case=False,
        smart_case=False,
        fixed_strings=False,
        word_regexp=False,
        test_string="development",
        should_match=False,
    ),
    CompileSearchPatternsFixture(
        test_id="ignore_case_match",
        pattern="DEV",
        ignore_case=True,
        smart_case=False,
        fixed_strings=False,
        word_regexp=False,
        test_string="development",
        should_match=True,
    ),
    CompileSearchPatternsFixture(
        test_id="smart_case_lowercase",
        pattern="dev",
        ignore_case=False,
        smart_case=True,
        fixed_strings=False,
        word_regexp=False,
        test_string="DEVELOPMENT",
        should_match=True,
    ),
    CompileSearchPatternsFixture(
        test_id="smart_case_uppercase_no_match",
        pattern="Dev",
        ignore_case=False,
        smart_case=True,
        fixed_strings=False,
        word_regexp=False,
        test_string="development",
        should_match=False,
    ),
    CompileSearchPatternsFixture(
        test_id="fixed_strings_literal",
        pattern="dev.*",
        ignore_case=False,
        smart_case=False,
        fixed_strings=True,
        word_regexp=False,
        test_string="dev.*project",
        should_match=True,
    ),
    CompileSearchPatternsFixture(
        test_id="fixed_strings_no_regex",
        pattern="dev.*",
        ignore_case=False,
        smart_case=False,
        fixed_strings=True,
        word_regexp=False,
        test_string="development",
        should_match=False,
    ),
    CompileSearchPatternsFixture(
        test_id="word_boundary_match",
        pattern="dev",
        ignore_case=False,
        smart_case=False,
        fixed_strings=False,
        word_regexp=True,
        test_string="my dev project",
        should_match=True,
    ),
    CompileSearchPatternsFixture(
        test_id="word_boundary_no_match",
        pattern="dev",
        ignore_case=False,
        smart_case=False,
        fixed_strings=False,
        word_regexp=True,
        test_string="development",
        should_match=False,
    ),
    CompileSearchPatternsFixture(
        test_id="regex_pattern",
        pattern="dev.*proj",
        ignore_case=False,
        smart_case=False,
        fixed_strings=False,
        word_regexp=False,
        test_string="dev-project",
        should_match=True,
    ),
]


@pytest.mark.parametrize(
    CompileSearchPatternsFixture._fields,
    COMPILE_SEARCH_PATTERNS_FIXTURES,
    ids=[test.test_id for test in COMPILE_SEARCH_PATTERNS_FIXTURES],
)
def test_compile_search_patterns(
    test_id: str,
    pattern: str,
    ignore_case: bool,
    smart_case: bool,
    fixed_strings: bool,
    word_regexp: bool,
    test_string: str,
    should_match: bool,
) -> None:
    """Test compile_search_patterns function."""
    tokens = [SearchToken(fields=("name",), pattern=pattern)]

    patterns = compile_search_patterns(
        tokens,
        ignore_case=ignore_case,
        smart_case=smart_case,
        fixed_strings=fixed_strings,
        word_regexp=word_regexp,
    )

    assert len(patterns) == 1
    match = patterns[0].regex.search(test_string)
    assert bool(match) == should_match


class TestExtractWorkspaceFields:
    """Tests for extract_workspace_fields."""

    def test_basic_extraction(self, tmp_path: pathlib.Path) -> None:
        """Extract fields from basic workspace file."""
        workspace = tmp_path / "test.yaml"
        workspace.write_text(
            "session_name: my-session\n"
            "windows:\n"
            "  - window_name: editor\n"
            "    panes:\n"
            "      - vim\n"
            "  - window_name: shell\n"
        )

        fields = extract_workspace_fields(workspace)

        assert fields["name"] == "test"
        assert fields["session_name"] == "my-session"
        assert "editor" in fields["windows"]
        assert "shell" in fields["windows"]
        assert "vim" in fields["panes"]

    def test_pane_shell_command_dict(self, tmp_path: pathlib.Path) -> None:
        """Extract pane commands from dict format."""
        workspace = tmp_path / "test.yaml"
        workspace.write_text(
            "session_name: test\n"
            "windows:\n"
            "  - window_name: main\n"
            "    panes:\n"
            "      - shell_command: git status\n"
            "      - shell_command:\n"
            "          - npm install\n"
            "          - npm start\n"
        )

        fields = extract_workspace_fields(workspace)

        assert "git status" in fields["panes"]
        assert "npm install" in fields["panes"]
        assert "npm start" in fields["panes"]

    def test_missing_session_name(self, tmp_path: pathlib.Path) -> None:
        """Handle workspace without session_name."""
        workspace = tmp_path / "test.yaml"
        workspace.write_text("windows:\n  - window_name: main\n")

        fields = extract_workspace_fields(workspace)

        assert fields["session_name"] == ""
        assert fields["name"] == "test"

    def test_invalid_yaml(self, tmp_path: pathlib.Path) -> None:
        """Handle invalid YAML gracefully."""
        workspace = tmp_path / "test.yaml"
        workspace.write_text("{{{{invalid yaml")

        fields = extract_workspace_fields(workspace)

        assert fields["name"] == "test"
        assert fields["session_name"] == ""
        assert fields["windows"] == []

    def test_path_uses_privacy(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Path should use PrivatePath for home contraction."""
        monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
        workspace = tmp_path / "test.yaml"
        workspace.write_text("session_name: test\n")

        fields = extract_workspace_fields(workspace)

        assert fields["path"] == "~/test.yaml"


class TestEvaluateMatch:
    """Tests for evaluate_match function."""

    @pytest.fixture()
    def sample_fields(self) -> WorkspaceFields:
        """Sample workspace fields for testing."""
        return WorkspaceFields(
            name="dev-project",
            path="~/.tmuxp/dev-project.yaml",
            session_name="development",
            windows=["editor", "shell", "logs"],
            panes=["vim", "git status", "tail -f"],
        )

    def test_single_pattern_match(self, sample_fields: WorkspaceFields) -> None:
        """Single pattern should match."""
        pattern = SearchPattern(
            fields=("name",),
            raw="dev",
            regex=re.compile("dev"),
        )

        matched, matches = evaluate_match(sample_fields, [pattern])

        assert matched is True
        assert "name" in matches

    def test_single_pattern_no_match(self, sample_fields: WorkspaceFields) -> None:
        """Single pattern should not match."""
        pattern = SearchPattern(
            fields=("name",),
            raw="xyz",
            regex=re.compile("xyz"),
        )

        matched, matches = evaluate_match(sample_fields, [pattern])

        assert matched is False
        assert matches == {}

    def test_and_logic_all_match(self, sample_fields: WorkspaceFields) -> None:
        """AND logic - all patterns match."""
        p1 = SearchPattern(fields=("name",), raw="dev", regex=re.compile("dev"))
        p2 = SearchPattern(fields=("name",), raw="project", regex=re.compile("project"))

        matched, _ = evaluate_match(sample_fields, [p1, p2], match_any=False)

        assert matched is True

    def test_and_logic_partial_no_match(self, sample_fields: WorkspaceFields) -> None:
        """AND logic - only some patterns match."""
        p1 = SearchPattern(fields=("name",), raw="dev", regex=re.compile("dev"))
        p2 = SearchPattern(fields=("name",), raw="xyz", regex=re.compile("xyz"))

        matched, _ = evaluate_match(sample_fields, [p1, p2], match_any=False)

        assert matched is False

    def test_or_logic_any_match(self, sample_fields: WorkspaceFields) -> None:
        """OR logic - any pattern matches."""
        p1 = SearchPattern(fields=("name",), raw="xyz", regex=re.compile("xyz"))
        p2 = SearchPattern(fields=("name",), raw="dev", regex=re.compile("dev"))

        matched, _ = evaluate_match(sample_fields, [p1, p2], match_any=True)

        assert matched is True

    def test_window_field_search(self, sample_fields: WorkspaceFields) -> None:
        """Search in window field."""
        pattern = SearchPattern(
            fields=("window",),
            raw="editor",
            regex=re.compile("editor"),
        )

        matched, matches = evaluate_match(sample_fields, [pattern])

        assert matched is True
        assert "window" in matches

    def test_pane_field_search(self, sample_fields: WorkspaceFields) -> None:
        """Search in pane field."""
        pattern = SearchPattern(
            fields=("pane",),
            raw="vim",
            regex=re.compile("vim"),
        )

        matched, matches = evaluate_match(sample_fields, [pattern])

        assert matched is True
        assert "pane" in matches

    def test_multiple_fields(self, sample_fields: WorkspaceFields) -> None:
        """Pattern searches multiple fields."""
        pattern = SearchPattern(
            fields=("name", "session_name"),
            raw="dev",
            regex=re.compile("dev"),
        )

        matched, matches = evaluate_match(sample_fields, [pattern])

        assert matched is True
        # Should find matches in both name and session_name
        assert "name" in matches or "session_name" in matches


class TestFindSearchMatches:
    """Tests for find_search_matches function."""

    def test_basic_search(self, tmp_path: pathlib.Path) -> None:
        """Basic search finds matching workspace."""
        workspace = tmp_path / "dev.yaml"
        workspace.write_text("session_name: development\n")

        pattern = SearchPattern(
            fields=("session_name",),
            raw="dev",
            regex=re.compile("dev"),
        )

        results = find_search_matches([(workspace, "global")], [pattern])

        assert len(results) == 1
        assert results[0]["source"] == "global"

    def test_no_match(self, tmp_path: pathlib.Path) -> None:
        """Search returns empty when no match."""
        workspace = tmp_path / "production.yaml"
        workspace.write_text("session_name: production\n")

        pattern = SearchPattern(
            fields=("name",),
            raw="dev",
            regex=re.compile("dev"),
        )

        results = find_search_matches([(workspace, "global")], [pattern])

        assert len(results) == 0

    def test_invert_match(self, tmp_path: pathlib.Path) -> None:
        """Invert match returns non-matching workspaces."""
        workspace = tmp_path / "production.yaml"
        workspace.write_text("session_name: production\n")

        pattern = SearchPattern(
            fields=("name",),
            raw="dev",
            regex=re.compile("dev"),
        )

        results = find_search_matches(
            [(workspace, "global")], [pattern], invert_match=True
        )

        assert len(results) == 1

    def test_multiple_workspaces(self, tmp_path: pathlib.Path) -> None:
        """Search across multiple workspaces."""
        ws1 = tmp_path / "dev.yaml"
        ws1.write_text("session_name: development\n")

        ws2 = tmp_path / "prod.yaml"
        ws2.write_text("session_name: production\n")

        pattern = SearchPattern(
            fields=("name", "session_name"),
            raw="dev",
            regex=re.compile("dev"),
        )

        results = find_search_matches([(ws1, "global"), (ws2, "global")], [pattern])

        assert len(results) == 1
        assert results[0]["fields"]["name"] == "dev"


class TestHighlightMatches:
    """Tests for highlight_matches function."""

    def test_no_colors(self) -> None:
        """Colors disabled returns original text."""
        colors = Colors(ColorMode.NEVER)
        pattern = SearchPattern(
            fields=("name",),
            raw="dev",
            regex=re.compile("dev"),
        )

        result = highlight_matches("development", [pattern], colors=colors)

        assert result == "development"

    def test_with_colors(self) -> None:
        """Colors enabled adds ANSI codes."""
        colors = Colors(ColorMode.ALWAYS)
        pattern = SearchPattern(
            fields=("name",),
            raw="dev",
            regex=re.compile("dev"),
        )

        result = highlight_matches("development", [pattern], colors=colors)

        assert "\033[" in result  # Contains ANSI escape
        assert "dev" in result

    def test_no_match(self) -> None:
        """No match returns original text."""
        colors = Colors(ColorMode.ALWAYS)
        pattern = SearchPattern(
            fields=("name",),
            raw="xyz",
            regex=re.compile("xyz"),
        )

        result = highlight_matches("development", [pattern], colors=colors)

        assert result == "development"

    def test_multiple_matches(self) -> None:
        """Multiple matches in same string."""
        colors = Colors(ColorMode.ALWAYS)
        pattern = SearchPattern(
            fields=("name",),
            raw="e",
            regex=re.compile("e"),
        )

        result = highlight_matches("development", [pattern], colors=colors)

        # Should contain multiple highlights
        assert result.count("\033[") > 1

    def test_empty_patterns(self) -> None:
        """Empty patterns returns original text."""
        colors = Colors(ColorMode.ALWAYS)

        result = highlight_matches("development", [], colors=colors)

        assert result == "development"


class TestGetFieldValues:
    """Tests for _get_field_values helper."""

    @pytest.fixture()
    def sample_fields(self) -> WorkspaceFields:
        """Sample workspace fields."""
        return WorkspaceFields(
            name="test",
            path="~/.tmuxp/test.yaml",
            session_name="test-session",
            windows=["editor", "shell"],
            panes=["vim", "bash"],
        )

    def test_scalar_field(self, sample_fields: WorkspaceFields) -> None:
        """Scalar field returns list with one item."""
        result = _get_field_values(sample_fields, "name")
        assert result == ["test"]

    def test_list_field(self, sample_fields: WorkspaceFields) -> None:
        """List field returns the list."""
        result = _get_field_values(sample_fields, "windows")
        assert result == ["editor", "shell"]

    def test_window_alias(self, sample_fields: WorkspaceFields) -> None:
        """Window alias maps to windows."""
        result = _get_field_values(sample_fields, "window")
        assert result == ["editor", "shell"]

    def test_pane_alias(self, sample_fields: WorkspaceFields) -> None:
        """Pane alias maps to panes."""
        result = _get_field_values(sample_fields, "pane")
        assert result == ["vim", "bash"]

    def test_empty_value(self) -> None:
        """Empty value returns empty list."""
        fields = WorkspaceFields(
            name="",
            path="",
            session_name="",
            windows=[],
            panes=[],
        )
        result = _get_field_values(fields, "name")
        assert result == []


class TestSearchSubparser:
    """Tests for search subparser configuration."""

    def test_parser_creation(self) -> None:
        """Subparser can be created successfully."""
        import argparse

        parser = argparse.ArgumentParser()
        result = create_search_subparser(parser)

        assert result is parser

    def test_parser_options(self) -> None:
        """Parser has expected options."""
        import argparse

        parser = argparse.ArgumentParser()
        create_search_subparser(parser)

        # Parse with various options
        args = parser.parse_args(["-i", "-S", "-F", "-w", "-v", "--any", "pattern"])

        assert args.ignore_case is True
        assert args.smart_case is True
        assert args.fixed_strings is True
        assert args.word_regexp is True
        assert args.invert_match is True
        assert args.match_any is True
        assert args.query_terms == ["pattern"]

    def test_output_format_options(self) -> None:
        """Parser supports output format options."""
        import argparse

        parser = argparse.ArgumentParser()
        create_search_subparser(parser)

        args_json = parser.parse_args(["--json", "test"])
        assert args_json.output_json is True

        args_ndjson = parser.parse_args(["--ndjson", "test"])
        assert args_ndjson.output_ndjson is True

    def test_field_option(self) -> None:
        """Parser supports field option."""
        import argparse

        parser = argparse.ArgumentParser()
        create_search_subparser(parser)

        args = parser.parse_args(["-f", "name", "-f", "session", "test"])

        assert args.field == ["name", "session"]


class TestOutputSearchResults:
    """Tests for _output_search_results function."""

    def test_no_results_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        """No results outputs warning message."""
        colors = Colors(ColorMode.NEVER)
        formatter = OutputFormatter(OutputMode.HUMAN)

        _output_search_results([], [], formatter, colors)
        formatter.finalize()

        captured = capsys.readouterr()
        assert "No matching" in captured.out

    def test_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """JSON output mode produces valid JSON."""
        colors = Colors(ColorMode.NEVER)
        formatter = OutputFormatter(OutputMode.JSON)

        result: WorkspaceSearchResult = {
            "filepath": "/test/dev.yaml",
            "source": "global",
            "fields": WorkspaceFields(
                name="dev",
                path="~/.tmuxp/dev.yaml",
                session_name="development",
                windows=["editor"],
                panes=["vim"],
            ),
            "matches": {"name": ["dev"]},
        }

        _output_search_results([result], [], formatter, colors)
        formatter.finalize()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["name"] == "dev"

    def test_ndjson_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """NDJSON output mode produces one JSON per line."""
        colors = Colors(ColorMode.NEVER)
        formatter = OutputFormatter(OutputMode.NDJSON)

        result: WorkspaceSearchResult = {
            "filepath": "/test/dev.yaml",
            "source": "global",
            "fields": WorkspaceFields(
                name="dev",
                path="~/.tmuxp/dev.yaml",
                session_name="development",
                windows=[],
                panes=[],
            ),
            "matches": {"name": ["dev"]},
        }

        _output_search_results([result], [], formatter, colors)
        formatter.finalize()

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        # Filter out human-readable lines
        json_lines = [line for line in lines if line.startswith("{")]
        assert len(json_lines) >= 1
        data = json.loads(json_lines[0])
        assert data["name"] == "dev"
