"""Tests for pretty_argparse sphinx extension."""

from __future__ import annotations

import typing as t

import pytest
from docutils import nodes
from pretty_argparse import (  # type: ignore[import-not-found]
    _is_examples_section,
    _is_usage_block,
    _reorder_nodes,
    escape_rst_emphasis,
    is_base_examples_term,
    is_examples_term,
    make_section_id,
    make_section_title,
    strip_ansi,
    transform_definition_list,
)

# --- strip_ansi tests ---


class StripAnsiFixture(t.NamedTuple):
    """Test fixture for strip_ansi function."""

    test_id: str
    input_text: str
    expected: str


STRIP_ANSI_FIXTURES: list[StripAnsiFixture] = [
    StripAnsiFixture(
        test_id="plain_text",
        input_text="hello",
        expected="hello",
    ),
    StripAnsiFixture(
        test_id="green_color",
        input_text="\033[32mgreen\033[0m",
        expected="green",
    ),
    StripAnsiFixture(
        test_id="bold_blue",
        input_text="\033[1;34mbold\033[0m",
        expected="bold",
    ),
    StripAnsiFixture(
        test_id="multiple_codes",
        input_text="\033[1m\033[32mtest\033[0m",
        expected="test",
    ),
    StripAnsiFixture(
        test_id="empty_string",
        input_text="",
        expected="",
    ),
    StripAnsiFixture(
        test_id="mixed_content",
        input_text="pre\033[31mred\033[0mpost",
        expected="preredpost",
    ),
    StripAnsiFixture(
        test_id="reset_only",
        input_text="\033[0m",
        expected="",
    ),
    StripAnsiFixture(
        test_id="sgr_params",
        input_text="\033[38;5;196mred256\033[0m",
        expected="red256",
    ),
]


@pytest.mark.parametrize(
    StripAnsiFixture._fields,
    STRIP_ANSI_FIXTURES,
    ids=[f.test_id for f in STRIP_ANSI_FIXTURES],
)
def test_strip_ansi(test_id: str, input_text: str, expected: str) -> None:
    """Test ANSI escape code stripping."""
    assert strip_ansi(input_text) == expected


# --- escape_rst_emphasis tests ---


class EscapeRstEmphasisFixture(t.NamedTuple):
    """Test fixture for escape_rst_emphasis function."""

    test_id: str
    input_text: str
    expected: str


ESCAPE_RST_EMPHASIS_FIXTURES: list[EscapeRstEmphasisFixture] = [
    EscapeRstEmphasisFixture(
        test_id="glob_pattern_escaped",
        input_text='tmuxp load "django-*"',
        expected='tmuxp load "django-\\*"',
    ),
    EscapeRstEmphasisFixture(
        test_id="multiple_glob_patterns",
        input_text='tmuxp load "flask-*" "django-*"',
        expected='tmuxp load "flask-\\*" "django-\\*"',
    ),
    EscapeRstEmphasisFixture(
        test_id="plain_text_unchanged",
        input_text="tmuxp load",
        expected="tmuxp load",
    ),
    EscapeRstEmphasisFixture(
        test_id="single_asterisk_unchanged",
        input_text="tmuxp load *",
        expected="tmuxp load *",
    ),
    EscapeRstEmphasisFixture(
        test_id="emphasis_unchanged",
        input_text="*emphasis* text",
        expected="*emphasis* text",
    ),
    EscapeRstEmphasisFixture(
        test_id="strong_unchanged",
        input_text="**strong** text",
        expected="**strong** text",
    ),
    EscapeRstEmphasisFixture(
        test_id="already_escaped_unchanged",
        input_text='tmuxp load "django-\\*"',
        expected='tmuxp load "django-\\*"',
    ),
    EscapeRstEmphasisFixture(
        test_id="hyphen_asterisk_space_unchanged",
        input_text="- * bullet",
        expected="- * bullet",
    ),
    EscapeRstEmphasisFixture(
        test_id="glob_at_end_of_string",
        input_text='Filter by "flask-*',
        expected='Filter by "flask-\\*',
    ),
    EscapeRstEmphasisFixture(
        test_id="underscore_asterisk_unchanged",
        input_text='Use pattern "my_*"',
        expected='Use pattern "my_*"',
    ),
    EscapeRstEmphasisFixture(
        test_id="hyphen_escaped_underscore_unchanged",
        input_text='"a-*" or "b_*" patterns',
        expected='"a-\\*" or "b_*" patterns',
    ),
    EscapeRstEmphasisFixture(
        test_id="empty_string",
        input_text="",
        expected="",
    ),
    EscapeRstEmphasisFixture(
        test_id="asterisk_in_word_unchanged",
        input_text="multi*plied value",
        expected="multi*plied value",
    ),
]


@pytest.mark.parametrize(
    EscapeRstEmphasisFixture._fields,
    ESCAPE_RST_EMPHASIS_FIXTURES,
    ids=[f.test_id for f in ESCAPE_RST_EMPHASIS_FIXTURES],
)
def test_escape_rst_emphasis(test_id: str, input_text: str, expected: str) -> None:
    """Test RST emphasis escaping for glob patterns."""
    assert escape_rst_emphasis(input_text) == expected


# --- is_examples_term tests ---


class IsExamplesTermFixture(t.NamedTuple):
    """Test fixture for is_examples_term function."""

    test_id: str
    term_text: str
    expected: bool


IS_EXAMPLES_TERM_FIXTURES: list[IsExamplesTermFixture] = [
    IsExamplesTermFixture(
        test_id="base_examples_colon",
        term_text="examples:",
        expected=True,
    ),
    IsExamplesTermFixture(
        test_id="base_examples_no_colon",
        term_text="examples",
        expected=True,
    ),
    IsExamplesTermFixture(
        test_id="prefixed_machine_readable",
        term_text="Machine-readable output examples:",
        expected=True,
    ),
    IsExamplesTermFixture(
        test_id="prefixed_field_scoped",
        term_text="Field-scoped search examples:",
        expected=True,
    ),
    IsExamplesTermFixture(
        test_id="colon_pattern",
        term_text="Machine-readable output: examples:",
        expected=True,
    ),
    IsExamplesTermFixture(
        test_id="usage_not_examples",
        term_text="Usage:",
        expected=False,
    ),
    IsExamplesTermFixture(
        test_id="arguments_not_examples",
        term_text="Named Arguments:",
        expected=False,
    ),
    IsExamplesTermFixture(
        test_id="case_insensitive_upper",
        term_text="EXAMPLES:",
        expected=True,
    ),
    IsExamplesTermFixture(
        test_id="case_insensitive_mixed",
        term_text="Examples:",
        expected=True,
    ),
]


@pytest.mark.parametrize(
    IsExamplesTermFixture._fields,
    IS_EXAMPLES_TERM_FIXTURES,
    ids=[f.test_id for f in IS_EXAMPLES_TERM_FIXTURES],
)
def test_is_examples_term(test_id: str, term_text: str, expected: bool) -> None:
    """Test examples term detection."""
    assert is_examples_term(term_text) == expected


# --- is_base_examples_term tests ---


class IsBaseExamplesTermFixture(t.NamedTuple):
    """Test fixture for is_base_examples_term function."""

    test_id: str
    term_text: str
    expected: bool


IS_BASE_EXAMPLES_TERM_FIXTURES: list[IsBaseExamplesTermFixture] = [
    IsBaseExamplesTermFixture(
        test_id="base_with_colon",
        term_text="examples:",
        expected=True,
    ),
    IsBaseExamplesTermFixture(
        test_id="base_no_colon",
        term_text="examples",
        expected=True,
    ),
    IsBaseExamplesTermFixture(
        test_id="uppercase",
        term_text="EXAMPLES",
        expected=True,
    ),
    IsBaseExamplesTermFixture(
        test_id="mixed_case",
        term_text="Examples:",
        expected=True,
    ),
    IsBaseExamplesTermFixture(
        test_id="prefixed_not_base",
        term_text="Field-scoped examples:",
        expected=False,
    ),
    IsBaseExamplesTermFixture(
        test_id="output_examples_not_base",
        term_text="Machine-readable output examples:",
        expected=False,
    ),
    IsBaseExamplesTermFixture(
        test_id="colon_pattern_not_base",
        term_text="Output: examples:",
        expected=False,
    ),
]


@pytest.mark.parametrize(
    IsBaseExamplesTermFixture._fields,
    IS_BASE_EXAMPLES_TERM_FIXTURES,
    ids=[f.test_id for f in IS_BASE_EXAMPLES_TERM_FIXTURES],
)
def test_is_base_examples_term(test_id: str, term_text: str, expected: bool) -> None:
    """Test base examples term detection."""
    assert is_base_examples_term(term_text) == expected


# --- make_section_id tests ---


class MakeSectionIdFixture(t.NamedTuple):
    """Test fixture for make_section_id function."""

    test_id: str
    term_text: str
    counter: int
    is_subsection: bool
    expected: str


MAKE_SECTION_ID_FIXTURES: list[MakeSectionIdFixture] = [
    MakeSectionIdFixture(
        test_id="base_examples",
        term_text="examples:",
        counter=0,
        is_subsection=False,
        expected="examples",
    ),
    MakeSectionIdFixture(
        test_id="prefixed_standard",
        term_text="Machine-readable output examples:",
        counter=0,
        is_subsection=False,
        expected="machine-readable-output-examples",
    ),
    MakeSectionIdFixture(
        test_id="subsection_omits_suffix",
        term_text="Field-scoped examples:",
        counter=0,
        is_subsection=True,
        expected="field-scoped",
    ),
    MakeSectionIdFixture(
        test_id="with_counter",
        term_text="examples:",
        counter=2,
        is_subsection=False,
        expected="examples-2",
    ),
    MakeSectionIdFixture(
        test_id="counter_zero_no_suffix",
        term_text="examples:",
        counter=0,
        is_subsection=False,
        expected="examples",
    ),
    MakeSectionIdFixture(
        test_id="colon_pattern",
        term_text="Machine-readable output: examples:",
        counter=0,
        is_subsection=False,
        expected="machine-readable-output-examples",
    ),
    MakeSectionIdFixture(
        test_id="subsection_with_counter",
        term_text="Field-scoped examples:",
        counter=1,
        is_subsection=True,
        expected="field-scoped-1",
    ),
]


@pytest.mark.parametrize(
    MakeSectionIdFixture._fields,
    MAKE_SECTION_ID_FIXTURES,
    ids=[f.test_id for f in MAKE_SECTION_ID_FIXTURES],
)
def test_make_section_id(
    test_id: str,
    term_text: str,
    counter: int,
    is_subsection: bool,
    expected: str,
) -> None:
    """Test section ID generation."""
    assert make_section_id(term_text, counter, is_subsection=is_subsection) == expected


# --- make_section_title tests ---


class MakeSectionTitleFixture(t.NamedTuple):
    """Test fixture for make_section_title function."""

    test_id: str
    term_text: str
    is_subsection: bool
    expected: str


MAKE_SECTION_TITLE_FIXTURES: list[MakeSectionTitleFixture] = [
    MakeSectionTitleFixture(
        test_id="base_examples",
        term_text="examples:",
        is_subsection=False,
        expected="Examples",
    ),
    MakeSectionTitleFixture(
        test_id="prefixed_with_examples_suffix",
        term_text="Machine-readable output examples:",
        is_subsection=False,
        expected="Machine-Readable Output Examples",
    ),
    MakeSectionTitleFixture(
        test_id="subsection_omits_examples",
        term_text="Field-scoped examples:",
        is_subsection=True,
        expected="Field-Scoped",
    ),
    MakeSectionTitleFixture(
        test_id="colon_pattern",
        term_text="Machine-readable output: examples:",
        is_subsection=False,
        expected="Machine-Readable Output Examples",
    ),
    MakeSectionTitleFixture(
        test_id="subsection_colon_pattern",
        term_text="Machine-readable output: examples:",
        is_subsection=True,
        expected="Machine-Readable Output",
    ),
    MakeSectionTitleFixture(
        test_id="base_examples_no_colon",
        term_text="examples",
        is_subsection=False,
        expected="Examples",
    ),
]


@pytest.mark.parametrize(
    MakeSectionTitleFixture._fields,
    MAKE_SECTION_TITLE_FIXTURES,
    ids=[f.test_id for f in MAKE_SECTION_TITLE_FIXTURES],
)
def test_make_section_title(
    test_id: str,
    term_text: str,
    is_subsection: bool,
    expected: str,
) -> None:
    """Test section title generation."""
    assert make_section_title(term_text, is_subsection=is_subsection) == expected


# --- transform_definition_list integration tests ---


def _make_dl_item(term: str, definition: str) -> nodes.definition_list_item:
    """Create a definition list item for testing.

    Parameters
    ----------
    term : str
        The definition term text.
    definition : str
        The definition content text.

    Returns
    -------
    nodes.definition_list_item
        A definition list item with term and definition.
    """
    item = nodes.definition_list_item()
    term_node = nodes.term(text=term)
    def_node = nodes.definition()
    def_node += nodes.paragraph(text=definition)
    item += term_node
    item += def_node
    return item


def test_transform_definition_list_single_examples() -> None:
    """Single examples section creates one section node."""
    dl = nodes.definition_list()
    dl += _make_dl_item("examples:", "tmuxp ls")

    result = transform_definition_list(dl)

    assert len(result) == 1
    assert isinstance(result[0], nodes.section)
    assert result[0]["ids"] == ["examples"]


def test_transform_definition_list_nested_examples() -> None:
    """Base examples with category creates nested sections."""
    dl = nodes.definition_list()
    dl += _make_dl_item("examples:", "tmuxp ls")
    dl += _make_dl_item("Machine-readable output examples:", "tmuxp ls --json")

    result = transform_definition_list(dl)

    # Should have single parent section containing nested subsection
    assert len(result) == 1
    parent = result[0]
    assert isinstance(parent, nodes.section)
    assert parent["ids"] == ["examples"]

    # Find nested subsection
    subsections = [c for c in parent.children if isinstance(c, nodes.section)]
    assert len(subsections) == 1
    assert subsections[0]["ids"] == ["machine-readable-output"]


def test_transform_definition_list_multiple_categories() -> None:
    """Multiple example categories all nest under parent."""
    dl = nodes.definition_list()
    dl += _make_dl_item("examples:", "tmuxp ls")
    dl += _make_dl_item("Field-scoped examples:", "tmuxp ls --field name")
    dl += _make_dl_item("Machine-readable output examples:", "tmuxp ls --json")

    result = transform_definition_list(dl)

    assert len(result) == 1
    parent = result[0]
    assert isinstance(parent, nodes.section)

    subsections = [c for c in parent.children if isinstance(c, nodes.section)]
    assert len(subsections) == 2


def test_transform_definition_list_preserves_non_examples() -> None:
    """Non-example items preserved as definition list."""
    dl = nodes.definition_list()
    dl += _make_dl_item("Usage:", "How to use this command")
    dl += _make_dl_item("examples:", "tmuxp ls")

    result = transform_definition_list(dl)

    # Should have both definition list (non-examples) and section (examples)
    has_dl = any(isinstance(n, nodes.definition_list) for n in result)
    has_section = any(isinstance(n, nodes.section) for n in result)
    assert has_dl, "Non-example items should be preserved as definition list"
    assert has_section, "Example items should become sections"


def test_transform_definition_list_no_examples() -> None:
    """Definition list without examples returns empty list."""
    dl = nodes.definition_list()
    dl += _make_dl_item("Usage:", "How to use")
    dl += _make_dl_item("Options:", "Available options")

    result = transform_definition_list(dl)

    # All items are non-examples, should return definition list
    assert len(result) == 1
    assert isinstance(result[0], nodes.definition_list)


def test_transform_definition_list_only_category_no_base() -> None:
    """Single category example without base examples stays flat."""
    dl = nodes.definition_list()
    dl += _make_dl_item("Machine-readable output examples:", "tmuxp ls --json")

    result = transform_definition_list(dl)

    # Without base "examples:", no nesting - just single section
    assert len(result) == 1
    assert isinstance(result[0], nodes.section)
    # Should have full title since it's not nested
    assert result[0]["ids"] == ["machine-readable-output-examples"]


def test_transform_definition_list_code_blocks_created() -> None:
    """Each command line becomes a separate code block."""
    dl = nodes.definition_list()
    dl += _make_dl_item("examples:", "cmd1\ncmd2\ncmd3")

    result = transform_definition_list(dl)

    section = result[0]
    code_blocks = [c for c in section.children if isinstance(c, nodes.literal_block)]
    assert len(code_blocks) == 3
    assert code_blocks[0].astext() == "$ cmd1"
    assert code_blocks[1].astext() == "$ cmd2"
    assert code_blocks[2].astext() == "$ cmd3"


def test_transform_definition_list_machine_readable_code_blocks() -> None:
    """Machine-readable output examples creates separate code blocks per line.

    Regression test: Ensures category example sections like "Machine-readable
    output examples:" split multi-line commands into separate code blocks,
    not clumped together as a single block.
    """
    dl = nodes.definition_list()
    dl += _make_dl_item(
        "Machine-readable output examples:",
        "tmuxp ls --json\ntmuxp ls --json --full\ntmuxp ls --ndjson",
    )

    result = transform_definition_list(dl)

    section = result[0]
    code_blocks = [c for c in section.children if isinstance(c, nodes.literal_block)]
    assert len(code_blocks) == 3, "Each command should be a separate code block"
    assert code_blocks[0].astext() == "$ tmuxp ls --json"
    assert code_blocks[1].astext() == "$ tmuxp ls --json --full"
    assert code_blocks[2].astext() == "$ tmuxp ls --ndjson"


# --- _is_usage_block tests ---


class IsUsageBlockFixture(t.NamedTuple):
    """Test fixture for _is_usage_block function."""

    test_id: str
    node_type: str
    node_text: str
    expected: bool


IS_USAGE_BLOCK_FIXTURES: list[IsUsageBlockFixture] = [
    IsUsageBlockFixture(
        test_id="literal_block_usage_lowercase",
        node_type="literal_block",
        node_text="usage: cmd [-h]",
        expected=True,
    ),
    IsUsageBlockFixture(
        test_id="literal_block_usage_uppercase",
        node_type="literal_block",
        node_text="Usage: tmuxp load",
        expected=True,
    ),
    IsUsageBlockFixture(
        test_id="literal_block_usage_leading_space",
        node_type="literal_block",
        node_text="  usage: cmd",
        expected=True,
    ),
    IsUsageBlockFixture(
        test_id="literal_block_not_usage",
        node_type="literal_block",
        node_text="some other text",
        expected=False,
    ),
    IsUsageBlockFixture(
        test_id="literal_block_usage_in_middle",
        node_type="literal_block",
        node_text="see usage: for more",
        expected=False,
    ),
    IsUsageBlockFixture(
        test_id="paragraph_with_usage",
        node_type="paragraph",
        node_text="usage: cmd",
        expected=False,
    ),
    IsUsageBlockFixture(
        test_id="section_node",
        node_type="section",
        node_text="",
        expected=False,
    ),
]


def _make_test_node(node_type: str, node_text: str) -> nodes.Node:
    """Create a test node of the specified type.

    Parameters
    ----------
    node_type : str
        Type of node to create ("literal_block", "paragraph", "section").
    node_text : str
        Text content for the node.

    Returns
    -------
    nodes.Node
        The created node.
    """
    if node_type == "literal_block":
        return nodes.literal_block(text=node_text)
    if node_type == "paragraph":
        return nodes.paragraph(text=node_text)
    if node_type == "section":
        return nodes.section()
    msg = f"Unknown node type: {node_type}"
    raise ValueError(msg)


@pytest.mark.parametrize(
    IsUsageBlockFixture._fields,
    IS_USAGE_BLOCK_FIXTURES,
    ids=[f.test_id for f in IS_USAGE_BLOCK_FIXTURES],
)
def test_is_usage_block(
    test_id: str,
    node_type: str,
    node_text: str,
    expected: bool,
) -> None:
    """Test usage block detection."""
    node = _make_test_node(node_type, node_text)
    assert _is_usage_block(node) == expected


# --- _is_examples_section tests ---


class IsExamplesSectionFixture(t.NamedTuple):
    """Test fixture for _is_examples_section function."""

    test_id: str
    node_type: str
    section_ids: list[str]
    expected: bool


IS_EXAMPLES_SECTION_FIXTURES: list[IsExamplesSectionFixture] = [
    IsExamplesSectionFixture(
        test_id="section_with_examples_id",
        node_type="section",
        section_ids=["examples"],
        expected=True,
    ),
    IsExamplesSectionFixture(
        test_id="section_with_prefixed_examples",
        node_type="section",
        section_ids=["machine-readable-output-examples"],
        expected=True,
    ),
    IsExamplesSectionFixture(
        test_id="section_with_uppercase_examples",
        node_type="section",
        section_ids=["EXAMPLES"],
        expected=True,
    ),
    IsExamplesSectionFixture(
        test_id="section_without_examples",
        node_type="section",
        section_ids=["positional-arguments"],
        expected=False,
    ),
    IsExamplesSectionFixture(
        test_id="section_with_multiple_ids",
        node_type="section",
        section_ids=["main-id", "examples-alias"],
        expected=True,
    ),
    IsExamplesSectionFixture(
        test_id="section_empty_ids",
        node_type="section",
        section_ids=[],
        expected=False,
    ),
    IsExamplesSectionFixture(
        test_id="paragraph_node",
        node_type="paragraph",
        section_ids=[],
        expected=False,
    ),
    IsExamplesSectionFixture(
        test_id="literal_block_node",
        node_type="literal_block",
        section_ids=[],
        expected=False,
    ),
]


def _make_section_node(node_type: str, section_ids: list[str]) -> nodes.Node:
    """Create a test node with optional section IDs.

    Parameters
    ----------
    node_type : str
        Type of node to create.
    section_ids : list[str]
        IDs to assign if creating a section.

    Returns
    -------
    nodes.Node
        The created node.
    """
    if node_type == "section":
        section = nodes.section()
        section["ids"] = section_ids
        return section
    if node_type == "paragraph":
        return nodes.paragraph()
    if node_type == "literal_block":
        return nodes.literal_block(text="examples")
    msg = f"Unknown node type: {node_type}"
    raise ValueError(msg)


@pytest.mark.parametrize(
    IsExamplesSectionFixture._fields,
    IS_EXAMPLES_SECTION_FIXTURES,
    ids=[f.test_id for f in IS_EXAMPLES_SECTION_FIXTURES],
)
def test_is_examples_section(
    test_id: str,
    node_type: str,
    section_ids: list[str],
    expected: bool,
) -> None:
    """Test examples section detection."""
    node = _make_section_node(node_type, section_ids)
    assert _is_examples_section(node) == expected


# --- _reorder_nodes tests ---


def _make_usage_node(text: str = "usage: cmd [-h]") -> nodes.literal_block:
    """Create a usage block node.

    Parameters
    ----------
    text : str
        Text content for the usage block.

    Returns
    -------
    nodes.literal_block
        A literal block node with usage text.
    """
    return nodes.literal_block(text=text)


def _make_examples_section(section_id: str = "examples") -> nodes.section:
    """Create an examples section node.

    Parameters
    ----------
    section_id : str
        The ID for the section.

    Returns
    -------
    nodes.section
        A section node with the specified ID.
    """
    section = nodes.section()
    section["ids"] = [section_id]
    return section


def test_reorder_nodes_usage_after_examples() -> None:
    """Usage block after examples gets moved before examples."""
    desc = nodes.paragraph(text="Description")
    examples = _make_examples_section()
    usage = _make_usage_node()

    # Create a non-examples section
    args_section = nodes.section()
    args_section["ids"] = ["arguments"]

    result = _reorder_nodes([desc, examples, usage, args_section])

    # Should be: desc, usage, examples, args
    assert len(result) == 4
    assert isinstance(result[0], nodes.paragraph)
    assert isinstance(result[1], nodes.literal_block)
    assert isinstance(result[2], nodes.section)
    assert result[2]["ids"] == ["examples"]
    assert isinstance(result[3], nodes.section)
    assert result[3]["ids"] == ["arguments"]


def test_reorder_nodes_no_examples() -> None:
    """Without examples, original order is preserved."""
    desc = nodes.paragraph(text="Description")
    usage = _make_usage_node()
    args = nodes.section()
    args["ids"] = ["arguments"]

    result = _reorder_nodes([desc, usage, args])

    # Order unchanged: desc, usage, args
    assert len(result) == 3
    assert isinstance(result[0], nodes.paragraph)
    assert isinstance(result[1], nodes.literal_block)
    assert isinstance(result[2], nodes.section)


def test_reorder_nodes_usage_already_before_examples() -> None:
    """When usage is already before examples, order is preserved."""
    desc = nodes.paragraph(text="Description")
    usage = _make_usage_node()
    examples = _make_examples_section()
    args = nodes.section()
    args["ids"] = ["arguments"]

    result = _reorder_nodes([desc, usage, examples, args])

    # Order should be: desc, usage, examples, args
    assert len(result) == 4
    assert isinstance(result[0], nodes.paragraph)
    assert isinstance(result[1], nodes.literal_block)
    assert isinstance(result[2], nodes.section)
    assert result[2]["ids"] == ["examples"]


def test_reorder_nodes_empty_list() -> None:
    """Empty input returns empty output."""
    result = _reorder_nodes([])
    assert result == []


def test_reorder_nodes_multiple_usage_blocks() -> None:
    """Multiple usage blocks are all moved before examples."""
    desc = nodes.paragraph(text="Description")
    examples = _make_examples_section()
    usage1 = _make_usage_node("usage: cmd1 [-h]")
    usage2 = _make_usage_node("usage: cmd2 [-v]")

    result = _reorder_nodes([desc, examples, usage1, usage2])

    # Should be: desc, usage1, usage2, examples
    assert len(result) == 4
    assert isinstance(result[0], nodes.paragraph)
    assert isinstance(result[1], nodes.literal_block)
    assert isinstance(result[2], nodes.literal_block)
    assert isinstance(result[3], nodes.section)


def test_reorder_nodes_multiple_examples_sections() -> None:
    """Multiple examples sections are grouped together."""
    desc = nodes.paragraph(text="Description")
    examples1 = _make_examples_section("examples")
    usage = _make_usage_node()
    examples2 = _make_examples_section("machine-readable-output-examples")
    args = nodes.section()
    args["ids"] = ["arguments"]

    result = _reorder_nodes([desc, examples1, usage, examples2, args])

    # Should be: desc, usage, examples1, examples2, args
    assert len(result) == 5
    assert isinstance(result[0], nodes.paragraph)
    assert isinstance(result[1], nodes.literal_block)
    assert result[2]["ids"] == ["examples"]
    assert result[3]["ids"] == ["machine-readable-output-examples"]
    assert result[4]["ids"] == ["arguments"]


def test_reorder_nodes_preserves_non_examples_after() -> None:
    """Non-examples nodes after examples stay at the end."""
    desc = nodes.paragraph(text="Description")
    examples = _make_examples_section()
    usage = _make_usage_node()
    epilog = nodes.paragraph(text="Epilog")

    result = _reorder_nodes([desc, examples, usage, epilog])

    # Should be: desc, usage, examples, epilog
    assert len(result) == 4
    assert result[0].astext() == "Description"
    assert isinstance(result[1], nodes.literal_block)
    assert isinstance(result[2], nodes.section)
    assert result[3].astext() == "Epilog"
