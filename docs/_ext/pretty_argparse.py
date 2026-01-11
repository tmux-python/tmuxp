"""Enhanced sphinx-argparse output formatting.

This extension wraps sphinx-argparse's directive to:
1. Remove ANSI escape codes that may be present when FORCE_COLOR is set
2. Convert "examples:" definition lists into proper documentation sections
3. Nest category-specific examples under a parent Examples section
4. Apply cli-usage syntax highlighting to usage blocks
5. Reorder sections so usage appears before examples
"""

from __future__ import annotations

import re
import typing as t

from docutils import nodes
from sphinxarg.ext import ArgParseDirective

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx

_ANSI_RE = re.compile(r"\033\[[;?0-9]*[a-zA-Z]")

# Match asterisks that trigger RST emphasis (preceded by delimiter like - or space)
# but NOT asterisks already escaped or in code/literal contexts
_RST_EMPHASIS_RE = re.compile(r"(?<=[^\s\\])-\*(?=[^\s*]|$)")


def escape_rst_emphasis(text: str) -> str:
    r"""Escape asterisks that would trigger RST inline emphasis.

    In reStructuredText, ``*text*`` creates emphasis. When argparse help text
    contains patterns like ``django-*``, the dash (a delimiter character) followed
    by asterisk triggers emphasis detection, causing warnings like:
    "Inline emphasis start-string without end-string."

    This function escapes such asterisks with a backslash so they render literally.

    Parameters
    ----------
    text : str
        Text potentially containing problematic asterisks.

    Returns
    -------
    str
        Text with asterisks escaped where needed.

    Examples
    --------
    >>> escape_rst_emphasis('tmuxp load "my-*"')
    'tmuxp load "my-\\*"'
    >>> escape_rst_emphasis("plain text")
    'plain text'
    >>> escape_rst_emphasis("already \\* escaped")
    'already \\* escaped'
    >>> escape_rst_emphasis("*emphasis* is ok")
    '*emphasis* is ok'
    """
    return _RST_EMPHASIS_RE.sub(r"-\*", text)


def strip_ansi(text: str) -> str:
    r"""Remove ANSI escape codes from text.

    Parameters
    ----------
    text : str
        Text potentially containing ANSI codes.

    Returns
    -------
    str
        Text with ANSI codes removed.

    Examples
    --------
    >>> strip_ansi("plain text")
    'plain text'
    >>> strip_ansi("\033[32mgreen\033[0m")
    'green'
    >>> strip_ansi("\033[1;34mbold blue\033[0m")
    'bold blue'
    """
    return _ANSI_RE.sub("", text)


def is_examples_term(term_text: str) -> bool:
    """Check if a definition term is an examples header.

    Parameters
    ----------
    term_text : str
        The text content of a definition term.

    Returns
    -------
    bool
        True if this is an examples header.

    Examples
    --------
    >>> is_examples_term("examples:")
    True
    >>> is_examples_term("Machine-readable output examples:")
    True
    >>> is_examples_term("Usage:")
    False
    """
    return term_text.lower().rstrip(":").endswith("examples")


def is_base_examples_term(term_text: str) -> bool:
    """Check if a definition term is a base "examples:" header (no prefix).

    Parameters
    ----------
    term_text : str
        The text content of a definition term.

    Returns
    -------
    bool
        True if this is just "examples:" with no category prefix.

    Examples
    --------
    >>> is_base_examples_term("examples:")
    True
    >>> is_base_examples_term("Examples")
    True
    >>> is_base_examples_term("Field-scoped examples:")
    False
    """
    return term_text.lower().rstrip(":").strip() == "examples"


def make_section_id(
    term_text: str, counter: int = 0, *, is_subsection: bool = False
) -> str:
    """Generate a section ID from an examples term.

    Parameters
    ----------
    term_text : str
        The examples term text (e.g., "Machine-readable output: examples:")
    counter : int
        Counter for uniqueness if multiple examples sections exist.
    is_subsection : bool
        If True, omit "-examples" suffix for cleaner nested IDs.

    Returns
    -------
    str
        A normalized section ID.

    Examples
    --------
    >>> make_section_id("examples:")
    'examples'
    >>> make_section_id("Machine-readable output examples:")
    'machine-readable-output-examples'
    >>> make_section_id("Field-scoped examples:", is_subsection=True)
    'field-scoped'
    >>> make_section_id("examples:", counter=1)
    'examples-1'
    """
    # Extract prefix before "examples" (e.g., "Machine-readable output")
    lower_text = term_text.lower().rstrip(":")
    if "examples" in lower_text:
        prefix = lower_text.rsplit("examples", 1)[0].strip()
        # Remove trailing colon from prefix (handles ": examples" pattern)
        prefix = prefix.rstrip(":").strip()
        if prefix:
            normalized_prefix = prefix.replace(" ", "-")
            # Subsections don't need "-examples" suffix
            if is_subsection:
                section_id = normalized_prefix
            else:
                section_id = f"{normalized_prefix}-examples"
        else:
            section_id = "examples"
    else:
        section_id = "examples"

    # Add counter suffix for uniqueness
    if counter > 0:
        section_id = f"{section_id}-{counter}"

    return section_id


def make_section_title(term_text: str, *, is_subsection: bool = False) -> str:
    """Generate a section title from an examples term.

    Parameters
    ----------
    term_text : str
        The examples term text (e.g., "Machine-readable output: examples:")
    is_subsection : bool
        If True, omit "Examples" suffix for cleaner nested titles.

    Returns
    -------
    str
        A proper title (e.g., "Machine-readable Output Examples" or just
        "Machine-Readable Output" if is_subsection=True).

    Examples
    --------
    >>> make_section_title("examples:")
    'Examples'
    >>> make_section_title("Machine-readable output examples:")
    'Machine-Readable Output Examples'
    >>> make_section_title("Field-scoped examples:", is_subsection=True)
    'Field-Scoped'
    """
    # Remove trailing colon and normalize
    text = term_text.rstrip(":").strip()
    # Handle base "examples:" case
    if text.lower() == "examples":
        return "Examples"

    # Extract the prefix (category name) before "examples"
    lower = text.lower()
    if lower.endswith(": examples"):
        prefix = text[: -len(": examples")]
    elif lower.endswith(" examples"):
        prefix = text[: -len(" examples")]
    else:
        prefix = text

    # Title case the prefix
    titled_prefix = prefix.title()

    # For subsections, just use the prefix (cleaner nested titles)
    if is_subsection:
        return titled_prefix

    # For top-level sections, append "Examples"
    return f"{titled_prefix} Examples"


def _create_example_section(
    term_text: str,
    def_node: nodes.definition,
    *,
    is_subsection: bool = False,
) -> nodes.section:
    """Create a section node for an examples item.

    Parameters
    ----------
    term_text : str
        The examples term text.
    def_node : nodes.definition
        The definition node containing example commands.
    is_subsection : bool
        If True, create a subsection with simpler title/id.

    Returns
    -------
    nodes.section
        A section node with title and code blocks.
    """
    section_id = make_section_id(term_text, is_subsection=is_subsection)
    section_title = make_section_title(term_text, is_subsection=is_subsection)

    section = nodes.section()
    section["ids"] = [section_id]
    section["names"] = [nodes.fully_normalize_name(section_title)]

    title = nodes.title(text=section_title)
    section += title

    # Extract commands from definition and create separate code blocks
    def_text = strip_ansi(def_node.astext())
    for line in def_text.split("\n"):
        line = line.strip()
        if line:
            code_block = nodes.literal_block(
                text=f"$ {line}",
                classes=["highlight-console"],
            )
            code_block["language"] = "console"
            section += code_block

    return section


def transform_definition_list(dl_node: nodes.definition_list) -> list[nodes.Node]:
    """Transform a definition list, converting examples items to code blocks.

    If there's a base "examples:" item followed by category-specific examples
    (e.g., "Field-scoped: examples:"), the categories are nested under the
    parent Examples section for cleaner ToC structure.

    Parameters
    ----------
    dl_node : nodes.definition_list
        A definition list node.

    Returns
    -------
    list[nodes.Node]
        Transformed nodes - code blocks for examples, original for others.
    """
    # First pass: collect examples and non-examples items separately
    example_items: list[tuple[str, nodes.definition]] = []  # (term_text, def_node)
    non_example_items: list[nodes.Node] = []
    base_examples_index: int | None = None

    for item in dl_node.children:
        if not isinstance(item, nodes.definition_list_item):
            continue

        # Get the term and definition
        term_node = None
        def_node = None
        for child in item.children:
            if isinstance(child, nodes.term):
                term_node = child
            elif isinstance(child, nodes.definition):
                def_node = child

        if term_node is None or def_node is None:
            non_example_items.append(item)
            continue

        term_text = strip_ansi(term_node.astext())

        if is_examples_term(term_text):
            if is_base_examples_term(term_text):
                base_examples_index = len(example_items)
            example_items.append((term_text, def_node))
        else:
            non_example_items.append(item)

    # Build result nodes
    result_nodes: list[nodes.Node] = []

    # Flush non-example items first (if any appeared before examples)
    if non_example_items:
        new_dl = nodes.definition_list()
        new_dl.extend(non_example_items)
        result_nodes.append(new_dl)

    # Determine nesting strategy
    # Nest if: there's a base "examples:" AND at least one other example category
    should_nest = base_examples_index is not None and len(example_items) > 1

    if should_nest and base_examples_index is not None:
        # Create parent "Examples" section
        base_term, base_def = example_items[base_examples_index]
        parent_section = _create_example_section(
            base_term, base_def, is_subsection=False
        )

        # Add other examples as nested subsections
        for i, (term_text, def_node) in enumerate(example_items):
            if i == base_examples_index:
                continue  # Skip the base (already used as parent)
            subsection = _create_example_section(
                term_text, def_node, is_subsection=True
            )
            parent_section += subsection

        result_nodes.append(parent_section)
    else:
        # No nesting - create flat sections (backwards compatible)
        for term_text, def_node in example_items:
            section = _create_example_section(term_text, def_node, is_subsection=False)
            result_nodes.append(section)

    return result_nodes


def process_node(node: nodes.Node) -> nodes.Node | list[nodes.Node]:
    """Process a node: strip ANSI codes and transform examples.

    Parameters
    ----------
    node : nodes.Node
        A docutils node to process.

    Returns
    -------
    nodes.Node | list[nodes.Node]
        The processed node(s).
    """
    # Handle text nodes - strip ANSI
    if isinstance(node, nodes.Text):
        cleaned = strip_ansi(node.astext())
        if cleaned != node.astext():
            return nodes.Text(cleaned)
        return node

    # Handle definition lists - transform examples
    if isinstance(node, nodes.definition_list):
        # Check if any items are examples
        has_examples = False
        for item in node.children:
            if isinstance(item, nodes.definition_list_item):
                for child in item.children:
                    if isinstance(child, nodes.term) and is_examples_term(
                        strip_ansi(child.astext())
                    ):
                        has_examples = True
                        break
            if has_examples:
                break

        if has_examples:
            return transform_definition_list(node)

    # Handle literal_block nodes - strip ANSI and apply usage highlighting
    if isinstance(node, nodes.literal_block):
        text = strip_ansi(node.astext())
        needs_update = text != node.astext()

        # Check if this is a usage block (starts with "usage:")
        is_usage_block = text.lstrip().lower().startswith("usage:")

        if needs_update or is_usage_block:
            new_block = nodes.literal_block(text=text)
            # Preserve attributes
            for attr in ("language", "classes"):
                if attr in node:
                    new_block[attr] = node[attr]
            # Apply cli-usage language to usage blocks
            if is_usage_block:
                new_block["language"] = "cli-usage"
            return new_block
        return node

    # Handle paragraph nodes - strip ANSI and lift sections out
    if isinstance(node, nodes.paragraph):
        # Process children and check if any become sections
        processed_children: list[nodes.Node] = []
        changed = False
        has_sections = False

        for child in node.children:
            if isinstance(child, nodes.Text):
                cleaned = strip_ansi(child.astext())
                if cleaned != child.astext():
                    processed_children.append(nodes.Text(cleaned))
                    changed = True
                else:
                    processed_children.append(child)
            else:
                result = process_node(child)
                if isinstance(result, list):
                    processed_children.extend(result)
                    changed = True
                    # Check if any results are sections
                    if any(isinstance(r, nodes.section) for r in result):
                        has_sections = True
                elif result is not child:
                    processed_children.append(result)
                    changed = True
                    if isinstance(result, nodes.section):
                        has_sections = True
                else:
                    processed_children.append(child)

        if not changed:
            return node

        # If no sections, return a normal paragraph
        if not has_sections:
            new_para = nodes.paragraph()
            new_para.extend(processed_children)
            return new_para

        # Sections found - lift them out of the paragraph
        # Return a list: [para_before, section1, section2, ..., para_after]
        result_nodes: list[nodes.Node] = []
        current_para_children: list[nodes.Node] = []

        for child in processed_children:
            if isinstance(child, nodes.section):
                # Flush current paragraph content
                if current_para_children:
                    para = nodes.paragraph()
                    para.extend(current_para_children)
                    result_nodes.append(para)
                    current_para_children = []
                # Add section as a sibling
                result_nodes.append(child)
            else:
                current_para_children.append(child)

        # Flush remaining paragraph content
        if current_para_children:
            para = nodes.paragraph()
            para.extend(current_para_children)
            result_nodes.append(para)

        return result_nodes

    # Recursively process children for other node types
    if hasattr(node, "children"):
        new_children: list[nodes.Node] = []
        children_changed = False
        for child in node.children:
            result = process_node(child)
            if isinstance(result, list):
                new_children.extend(result)
                children_changed = True
            elif result is not child:
                new_children.append(result)
                children_changed = True
            else:
                new_children.append(child)
        if children_changed:
            node.children = new_children

    return node


def _is_usage_block(node: nodes.Node) -> bool:
    """Check if a node is a usage literal block.

    Parameters
    ----------
    node : nodes.Node
        A docutils node to check.

    Returns
    -------
    bool
        True if this is a usage block (literal_block starting with "usage:").

    Examples
    --------
    >>> from docutils import nodes
    >>> _is_usage_block(nodes.literal_block(text="usage: cmd [-h]"))
    True
    >>> _is_usage_block(nodes.literal_block(text="Usage: tmuxp load"))
    True
    >>> _is_usage_block(nodes.literal_block(text="  usage: cmd"))
    True
    >>> _is_usage_block(nodes.literal_block(text="some other text"))
    False
    >>> _is_usage_block(nodes.paragraph(text="usage: cmd"))
    False
    >>> _is_usage_block(nodes.section())
    False
    """
    if not isinstance(node, nodes.literal_block):
        return False
    text = node.astext()
    return text.lstrip().lower().startswith("usage:")


def _is_examples_section(node: nodes.Node) -> bool:
    """Check if a node is an examples section.

    Parameters
    ----------
    node : nodes.Node
        A docutils node to check.

    Returns
    -------
    bool
        True if this is an examples section (section with "examples" in its ID).

    Examples
    --------
    >>> from docutils import nodes
    >>> section = nodes.section()
    >>> section["ids"] = ["examples"]
    >>> _is_examples_section(section)
    True
    >>> section2 = nodes.section()
    >>> section2["ids"] = ["machine-readable-output-examples"]
    >>> _is_examples_section(section2)
    True
    >>> section3 = nodes.section()
    >>> section3["ids"] = ["positional-arguments"]
    >>> _is_examples_section(section3)
    False
    >>> _is_examples_section(nodes.paragraph())
    False
    >>> _is_examples_section(nodes.literal_block(text="examples"))
    False
    """
    if not isinstance(node, nodes.section):
        return False
    ids: list[str] = node.get("ids", [])
    return any("examples" in id_str.lower() for id_str in ids)


def _reorder_nodes(processed: list[nodes.Node]) -> list[nodes.Node]:
    """Reorder nodes so usage blocks appear before examples sections.

    This ensures the CLI usage synopsis appears above examples in the
    documentation, making it easier to understand command syntax before
    seeing example invocations.

    Parameters
    ----------
    processed : list[nodes.Node]
        List of processed docutils nodes.

    Returns
    -------
    list[nodes.Node]
        Reordered nodes with usage before examples.

    Examples
    --------
    >>> from docutils import nodes

    Create test nodes:

    >>> desc = nodes.paragraph(text="Description")
    >>> examples = nodes.section()
    >>> examples["ids"] = ["examples"]
    >>> usage = nodes.literal_block(text="usage: cmd [-h]")
    >>> args = nodes.section()
    >>> args["ids"] = ["arguments"]

    When usage appears after examples, it gets moved before:

    >>> result = _reorder_nodes([desc, examples, usage, args])
    >>> [type(n).__name__ for n in result]
    ['paragraph', 'literal_block', 'section', 'section']

    When no examples exist, order is unchanged:

    >>> result = _reorder_nodes([desc, usage, args])
    >>> [type(n).__name__ for n in result]
    ['paragraph', 'literal_block', 'section']

    When usage already before examples, order is preserved:

    >>> result = _reorder_nodes([desc, usage, examples, args])
    >>> [type(n).__name__ for n in result]
    ['paragraph', 'literal_block', 'section', 'section']

    Empty list returns empty:

    >>> _reorder_nodes([])
    []
    """
    # First pass: check if there are any examples sections
    has_examples = any(_is_examples_section(node) for node in processed)
    if not has_examples:
        # No examples, preserve original order
        return processed

    usage_blocks: list[nodes.Node] = []
    examples_sections: list[nodes.Node] = []
    other_before_examples: list[nodes.Node] = []
    other_after_examples: list[nodes.Node] = []

    seen_examples = False
    for node in processed:
        if _is_usage_block(node):
            usage_blocks.append(node)
        elif _is_examples_section(node):
            examples_sections.append(node)
            seen_examples = True
        elif not seen_examples:
            other_before_examples.append(node)
        else:
            other_after_examples.append(node)

    # Order: before_examples → usage → examples → after_examples
    return (
        other_before_examples + usage_blocks + examples_sections + other_after_examples
    )


class CleanArgParseDirective(ArgParseDirective):  # type: ignore[misc]
    """ArgParse directive that strips ANSI codes and formats examples."""

    def _nested_parse_paragraph(self, text: str) -> nodes.Node:
        """Parse text as RST, escaping problematic characters first.

        Overrides the parent class to escape asterisks in patterns like
        ``session-*`` that would otherwise trigger RST emphasis warnings.
        """
        escaped_text = escape_rst_emphasis(text)
        result: nodes.Node = super()._nested_parse_paragraph(escaped_text)
        return result

    def run(self) -> list[nodes.Node]:
        """Run the directive, clean output, format examples, and reorder."""
        result = super().run()

        processed: list[nodes.Node] = []
        for node in result:
            processed_node = process_node(node)
            if isinstance(processed_node, list):
                processed.extend(processed_node)
            else:
                processed.append(processed_node)

        # Reorder: usage blocks before examples sections
        return _reorder_nodes(processed)


def setup(app: Sphinx) -> dict[str, t.Any]:
    """Register the clean argparse directive and CLI usage lexer.

    Parameters
    ----------
    app : Sphinx
        The Sphinx application object.

    Returns
    -------
    dict
        Extension metadata.
    """
    # Override the default argparse directive
    app.add_directive("argparse", CleanArgParseDirective, override=True)

    # Register CLI usage lexer for usage block highlighting
    from cli_usage_lexer import CLIUsageLexer

    app.add_lexer("cli-usage", CLIUsageLexer)

    return {"version": "2.0", "parallel_read_safe": True}
