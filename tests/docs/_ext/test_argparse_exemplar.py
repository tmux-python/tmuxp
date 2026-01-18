"""Tests for argparse_exemplar sphinx extension.

This tests the examples transformation functionality that converts argparse
epilog definition lists into proper documentation sections.

Note: Tests for strip_ansi have moved to
tests/docs/_ext/sphinx_argparse_neo/test_utils.py since that utility
now lives in sphinx_argparse_neo.utils.
"""

from __future__ import annotations

import typing as t

import pytest
from argparse_exemplar import (  # type: ignore[import-not-found]
    ExemplarConfig,
    _is_examples_section,
    _is_usage_block,
    _reorder_nodes,
    is_base_examples_term,
    is_examples_term,
    make_section_id,
    make_section_title,
    transform_definition_list,
)
from docutils import nodes

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


def test_make_section_id_with_page_prefix() -> None:
    """Test section ID generation with page_prefix for cross-page uniqueness."""
    # Base "examples:" with page_prefix becomes "sync-examples"
    assert make_section_id("examples:", page_prefix="sync") == "sync-examples"
    assert make_section_id("examples:", page_prefix="add") == "add-examples"

    # Prefixed examples already unique - page_prefix not added
    assert (
        make_section_id("Machine-readable output examples:", page_prefix="sync")
        == "machine-readable-output-examples"
    )

    # Subsection with page_prefix
    result = make_section_id(
        "Field-scoped examples:", is_subsection=True, page_prefix="sync"
    )
    assert result == "field-scoped"

    # Empty page_prefix behaves like before
    assert make_section_id("examples:", page_prefix="") == "examples"


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
    dl += _make_dl_item("examples:", "vcspull ls")

    result = transform_definition_list(dl)

    assert len(result) == 1
    assert isinstance(result[0], nodes.section)
    assert result[0]["ids"] == ["examples"]


def test_transform_definition_list_nested_examples() -> None:
    """Base examples with category creates nested sections."""
    dl = nodes.definition_list()
    dl += _make_dl_item("examples:", "vcspull ls")
    dl += _make_dl_item("Machine-readable output examples:", "vcspull ls --json")

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
    dl += _make_dl_item("examples:", "vcspull ls")
    dl += _make_dl_item("Field-scoped examples:", "vcspull ls --field name")
    dl += _make_dl_item("Machine-readable output examples:", "vcspull ls --json")

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
    dl += _make_dl_item("examples:", "vcspull ls")

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
    dl += _make_dl_item("Machine-readable output examples:", "vcspull ls --json")

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
        node_text="Usage: vcspull sync",
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


# --- ExemplarConfig tests ---


def test_exemplar_config_defaults() -> None:
    """ExemplarConfig has sensible defaults."""
    config = ExemplarConfig()

    assert config.examples_term_suffix == "examples"
    assert config.examples_base_term == "examples"
    assert config.examples_section_title == "Examples"
    assert config.usage_pattern == "usage:"
    assert config.command_prefix == "$ "
    assert config.code_language == "console"
    assert config.code_classes == ("highlight-console",)
    assert config.usage_code_language == "cli-usage"
    assert config.reorder_usage_before_examples is True


def test_exemplar_config_custom_values() -> None:
    """ExemplarConfig accepts custom values."""
    config = ExemplarConfig(
        examples_term_suffix="demos",
        examples_base_term="demos",
        examples_section_title="Demos",
        usage_pattern="synopsis:",
        command_prefix="> ",
        code_language="bash",
        code_classes=("highlight-bash",),
        usage_code_language="cli-synopsis",
        reorder_usage_before_examples=False,
    )

    assert config.examples_term_suffix == "demos"
    assert config.examples_base_term == "demos"
    assert config.examples_section_title == "Demos"
    assert config.usage_pattern == "synopsis:"
    assert config.command_prefix == "> "
    assert config.code_language == "bash"
    assert config.code_classes == ("highlight-bash",)
    assert config.usage_code_language == "cli-synopsis"
    assert config.reorder_usage_before_examples is False


# --- Config integration tests ---


def test_is_examples_term_with_custom_config() -> None:
    """is_examples_term respects custom config."""
    config = ExemplarConfig(examples_term_suffix="demos")

    # Custom term should match
    assert is_examples_term("demos:", config=config) is True
    assert is_examples_term("Machine-readable output demos:", config=config) is True

    # Default term should not match
    assert is_examples_term("examples:", config=config) is False


def test_is_base_examples_term_with_custom_config() -> None:
    """is_base_examples_term respects custom config."""
    config = ExemplarConfig(examples_base_term="demos")

    # Custom term should match
    assert is_base_examples_term("demos:", config=config) is True
    assert is_base_examples_term("Demos", config=config) is True

    # Default term should not match
    assert is_base_examples_term("examples:", config=config) is False

    # Prefixed term should not match (not base)
    assert is_base_examples_term("Output demos:", config=config) is False


def test_make_section_id_with_custom_config() -> None:
    """make_section_id respects custom config."""
    config = ExemplarConfig(examples_term_suffix="demos")

    assert make_section_id("demos:", config=config) == "demos"
    assert (
        make_section_id("Machine-readable output demos:", config=config)
        == "machine-readable-output-demos"
    )
    assert (
        make_section_id("Field-scoped demos:", is_subsection=True, config=config)
        == "field-scoped"
    )


def test_make_section_title_with_custom_config() -> None:
    """make_section_title respects custom config."""
    config = ExemplarConfig(
        examples_base_term="demos",
        examples_term_suffix="demos",
        examples_section_title="Demos",
    )

    assert make_section_title("demos:", config=config) == "Demos"
    assert (
        make_section_title("Machine-readable output demos:", config=config)
        == "Machine-Readable Output Demos"
    )
    assert (
        make_section_title("Field-scoped demos:", is_subsection=True, config=config)
        == "Field-Scoped"
    )


def test_is_usage_block_with_custom_config() -> None:
    """_is_usage_block respects custom config."""
    config = ExemplarConfig(usage_pattern="synopsis:")

    # Custom pattern should match
    assert (
        _is_usage_block(nodes.literal_block(text="synopsis: cmd [-h]"), config=config)
        is True
    )
    assert (
        _is_usage_block(nodes.literal_block(text="Synopsis: cmd"), config=config)
        is True
    )

    # Default pattern should not match
    assert (
        _is_usage_block(nodes.literal_block(text="usage: cmd [-h]"), config=config)
        is False
    )


def test_is_examples_section_with_custom_config() -> None:
    """_is_examples_section respects custom config."""
    config = ExemplarConfig(examples_term_suffix="demos")

    # Custom term should match
    demos_section = nodes.section()
    demos_section["ids"] = ["demos"]
    assert _is_examples_section(demos_section, config=config) is True

    prefixed_demos = nodes.section()
    prefixed_demos["ids"] = ["output-demos"]
    assert _is_examples_section(prefixed_demos, config=config) is True

    # Default term should not match
    examples_section = nodes.section()
    examples_section["ids"] = ["examples"]
    assert _is_examples_section(examples_section, config=config) is False


def test_reorder_nodes_disabled_via_config() -> None:
    """Reordering can be disabled via config."""
    config = ExemplarConfig(reorder_usage_before_examples=False)

    desc = nodes.paragraph(text="Description")
    examples = _make_examples_section()
    usage = _make_usage_node()

    # Original order: desc, examples, usage
    result = _reorder_nodes([desc, examples, usage], config=config)

    # Order should be preserved (not reordered)
    assert len(result) == 3
    assert isinstance(result[0], nodes.paragraph)
    assert isinstance(result[1], nodes.section)  # examples still in position 1
    assert isinstance(result[2], nodes.literal_block)  # usage still at end


def test_transform_definition_list_with_custom_config() -> None:
    """transform_definition_list respects custom config."""
    config = ExemplarConfig(
        examples_term_suffix="demos",
        examples_base_term="demos",
        examples_section_title="Demos",
        command_prefix="> ",
        code_language="bash",
        code_classes=("highlight-bash",),
    )

    dl = nodes.definition_list()
    dl += _make_dl_item("demos:", "cmd1")

    result = transform_definition_list(dl, config=config)

    # Should create a section with "demos" id
    assert len(result) == 1
    section = result[0]
    assert isinstance(section, nodes.section)
    assert section["ids"] == ["demos"]

    # Find the title
    titles = [c for c in section.children if isinstance(c, nodes.title)]
    assert len(titles) == 1
    assert titles[0].astext() == "Demos"

    # Find code blocks
    code_blocks = [c for c in section.children if isinstance(c, nodes.literal_block)]
    assert len(code_blocks) == 1
    assert code_blocks[0].astext() == "> cmd1"  # Custom prefix
    assert code_blocks[0]["language"] == "bash"
    assert "highlight-bash" in code_blocks[0]["classes"]
