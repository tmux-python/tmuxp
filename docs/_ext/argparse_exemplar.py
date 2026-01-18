"""Transform argparse epilog "examples:" definition lists into documentation sections.

This Sphinx extension post-processes sphinx_argparse_neo output to convert
specially-formatted "examples:" definition lists in argparse epilogs into
proper documentation sections with syntax-highlighted code blocks.

The extension is designed to be generic and reusable across different projects.
All behavior can be customized via Sphinx configuration options.

Purpose
-------
When documenting CLI tools with argparse, it's useful to include examples in
the epilog. This extension recognizes a specific definition list format and
transforms it into structured documentation sections that appear in the TOC.

Input Format
------------
Format your argparse epilog with definition lists where terms end with "examples:":

.. code-block:: python

    parser = argparse.ArgumentParser(
        epilog=textwrap.dedent('''
            examples:
                myapp sync
                myapp sync myrepo

            Machine-readable output examples:
                myapp sync --json
                myapp sync -F json myrepo
        '''),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

The epilog text will be parsed as a definition list by docutils, with:
- Terms: "examples:", "Machine-readable output examples:", etc.
- Definitions: The example commands (one per line)

Output
------
The extension transforms these into proper sections:

- A base "examples:" term creates an "Examples" section
- Category-prefixed terms like "Machine-readable output examples:" create
  subsections nested under the parent Examples section
- Each command line becomes a syntax-highlighted console code block

Configuration
-------------
Configure via conf.py. All options have sensible defaults.

**Term Detection:**

``argparse_examples_term_suffix`` : str (default: "examples")
    Term must end with this string to be treated as an examples header.

``argparse_examples_base_term`` : str (default: "examples")
    Exact match for the base examples section (case-insensitive).

``argparse_examples_section_title`` : str (default: "Examples")
    Title used for the base examples section.

**Usage Detection:**

``argparse_usage_pattern`` : str (default: "usage:")
    Text must start with this to be treated as a usage block (case-insensitive).

**Code Block Formatting:**

``argparse_examples_command_prefix`` : str (default: "$ ")
    Prefix added to each command line in examples code blocks.

``argparse_examples_code_language`` : str (default: "console")
    Language identifier for examples code blocks.

``argparse_examples_code_classes`` : list[str] (default: ["highlight-console"])
    CSS classes added to examples code blocks.

``argparse_usage_code_language`` : str (default: "cli-usage")
    Language identifier for usage blocks.

**Behavior:**

``argparse_reorder_usage_before_examples`` : bool (default: True)
    Whether to reorder nodes so usage appears before examples.

Additional Features
-------------------
- Removes ANSI escape codes (useful when FORCE_COLOR is set)
- Applies syntax highlighting to usage blocks
- Reorders sections so usage appears before examples in the output
- Extracts sections from argparse_program containers for TOC visibility

Project-Specific Setup
----------------------
Projects using this extension should register their own lexers and CSS in
their conf.py setup() function. For example::

    def setup(app):
        from my_lexer import MyLexer
        app.add_lexer("my-output", MyLexer)
        app.add_css_file("css/my-highlight.css")
"""

from __future__ import annotations

import dataclasses
import typing as t

from docutils import nodes
from sphinx_argparse_neo.directive import ArgparseDirective
from sphinx_argparse_neo.utils import strip_ansi

if t.TYPE_CHECKING:
    import sphinx.config
    from sphinx.application import Sphinx


@dataclasses.dataclass
class ExemplarConfig:
    """Configuration for argparse_exemplar transformation.

    This dataclass provides all configurable options for the argparse_exemplar
    extension. Functions accept an optional config parameter with a factory
    default, allowing them to work standalone with defaults or accept custom
    config for full control.

    Attributes
    ----------
    examples_term_suffix : str
        Term must end with this string (case-insensitive) to be treated as an
        examples header. Default: "examples".
    examples_base_term : str
        Exact match (case-insensitive, after stripping ":") for the base
        examples section. Default: "examples".
    examples_section_title : str
        Title used for the base examples section. Default: "Examples".
    usage_pattern : str
        Text must start with this string (case-insensitive, after stripping
        whitespace) to be treated as a usage block. Default: "usage:".
    command_prefix : str
        Prefix added to each command line in examples code blocks.
        Default: "$ ".
    code_language : str
        Language identifier for examples code blocks. Default: "console".
    code_classes : tuple[str, ...]
        CSS classes added to examples code blocks.
        Default: ("highlight-console",).
    usage_code_language : str
        Language identifier for usage blocks. Default: "cli-usage".
    reorder_usage_before_examples : bool
        Whether to reorder nodes so usage appears before examples.
        Default: True.

    Examples
    --------
    Using default configuration:

    >>> config = ExemplarConfig()
    >>> config.examples_term_suffix
    'examples'
    >>> config.command_prefix
    '$ '

    Custom configuration:

    >>> config = ExemplarConfig(
    ...     command_prefix="> ",
    ...     code_language="bash",
    ... )
    >>> config.command_prefix
    '> '
    >>> config.code_language
    'bash'
    """

    # Term detection
    examples_term_suffix: str = "examples"
    examples_base_term: str = "examples"
    examples_section_title: str = "Examples"

    # Usage detection
    usage_pattern: str = "usage:"

    # Code block formatting
    command_prefix: str = "$ "
    code_language: str = "console"
    code_classes: tuple[str, ...] = ("highlight-console",)
    usage_code_language: str = "cli-usage"

    # Behavior
    reorder_usage_before_examples: bool = True

    @classmethod
    def from_sphinx_config(cls, config: sphinx.config.Config) -> ExemplarConfig:
        """Create ExemplarConfig from Sphinx configuration.

        Parameters
        ----------
        config : sphinx.config.Config
            The Sphinx configuration object.

        Returns
        -------
        ExemplarConfig
            Configuration populated from Sphinx config values.

        Examples
        --------
        This is typically called from a directive's run() method:

        >>> # In CleanArgParseDirective.run():
        >>> # config = ExemplarConfig.from_sphinx_config(self.env.config)
        """
        # Get code_classes as tuple (Sphinx stores lists)
        code_classes_raw = getattr(
            config, "argparse_examples_code_classes", ("highlight-console",)
        )
        code_classes = (
            tuple(code_classes_raw)
            if isinstance(code_classes_raw, list)
            else code_classes_raw
        )

        return cls(
            examples_term_suffix=getattr(
                config, "argparse_examples_term_suffix", "examples"
            ),
            examples_base_term=getattr(
                config, "argparse_examples_base_term", "examples"
            ),
            examples_section_title=getattr(
                config, "argparse_examples_section_title", "Examples"
            ),
            usage_pattern=getattr(config, "argparse_usage_pattern", "usage:"),
            command_prefix=getattr(config, "argparse_examples_command_prefix", "$ "),
            code_language=getattr(config, "argparse_examples_code_language", "console"),
            code_classes=code_classes,
            usage_code_language=getattr(
                config, "argparse_usage_code_language", "cli-usage"
            ),
            reorder_usage_before_examples=getattr(
                config, "argparse_reorder_usage_before_examples", True
            ),
        )


# Re-export for backwards compatibility and public API
__all__ = [
    "CleanArgParseDirective",
    "ExemplarConfig",
    "is_base_examples_term",
    "is_examples_term",
    "make_section_id",
    "make_section_title",
    "process_node",
    "strip_ansi",
    "transform_definition_list",
]


def is_examples_term(term_text: str, *, config: ExemplarConfig | None = None) -> bool:
    """Check if a definition term is an examples header.

    Parameters
    ----------
    term_text : str
        The text content of a definition term.
    config : ExemplarConfig | None
        Optional configuration. If None, uses default ExemplarConfig().

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

    With custom configuration:

    >>> custom_config = ExemplarConfig(examples_term_suffix="demos")
    >>> is_examples_term("demos:", config=custom_config)
    True
    >>> is_examples_term("examples:", config=custom_config)
    False
    """
    config = config or ExemplarConfig()
    return term_text.lower().rstrip(":").endswith(config.examples_term_suffix)


def is_base_examples_term(
    term_text: str, *, config: ExemplarConfig | None = None
) -> bool:
    """Check if a definition term is a base "examples:" header (no prefix).

    Parameters
    ----------
    term_text : str
        The text content of a definition term.
    config : ExemplarConfig | None
        Optional configuration. If None, uses default ExemplarConfig().

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

    With custom configuration:

    >>> custom_config = ExemplarConfig(examples_base_term="demos")
    >>> is_base_examples_term("demos:", config=custom_config)
    True
    >>> is_base_examples_term("examples:", config=custom_config)
    False
    """
    config = config or ExemplarConfig()
    return term_text.lower().rstrip(":").strip() == config.examples_base_term


def make_section_id(
    term_text: str,
    counter: int = 0,
    *,
    is_subsection: bool = False,
    page_prefix: str = "",
    config: ExemplarConfig | None = None,
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
    page_prefix : str
        Optional prefix from the page name (e.g., "sync", "add") to ensure
        uniqueness across different documentation pages.
    config : ExemplarConfig | None
        Optional configuration. If None, uses default ExemplarConfig().

    Returns
    -------
    str
        A normalized section ID.

    Examples
    --------
    >>> make_section_id("examples:")
    'examples'
    >>> make_section_id("examples:", page_prefix="sync")
    'sync-examples'
    >>> make_section_id("Machine-readable output examples:")
    'machine-readable-output-examples'
    >>> make_section_id("Field-scoped examples:", is_subsection=True)
    'field-scoped'
    >>> make_section_id("examples:", counter=1)
    'examples-1'

    With custom configuration:

    >>> custom_config = ExemplarConfig(examples_term_suffix="demos")
    >>> make_section_id("demos:", config=custom_config)
    'demos'
    >>> make_section_id("Machine-readable output demos:", config=custom_config)
    'machine-readable-output-demos'
    """
    config = config or ExemplarConfig()
    term_suffix = config.examples_term_suffix

    # Extract prefix before the term suffix (e.g., "Machine-readable output")
    lower_text = term_text.lower().rstrip(":")
    if term_suffix in lower_text:
        prefix = lower_text.rsplit(term_suffix, 1)[0].strip()
        # Remove trailing colon from prefix (handles ": examples" pattern)
        prefix = prefix.rstrip(":").strip()
        if prefix:
            normalized_prefix = prefix.replace(" ", "-")
            # Subsections don't need "-examples" suffix
            if is_subsection:
                section_id = normalized_prefix
            else:
                section_id = f"{normalized_prefix}-{term_suffix}"
        else:
            # Plain "examples" - add page prefix if provided for uniqueness
            section_id = f"{page_prefix}-{term_suffix}" if page_prefix else term_suffix
    else:
        section_id = term_suffix

    # Add counter suffix for uniqueness
    if counter > 0:
        section_id = f"{section_id}-{counter}"

    return section_id


def make_section_title(
    term_text: str,
    *,
    is_subsection: bool = False,
    config: ExemplarConfig | None = None,
) -> str:
    """Generate a section title from an examples term.

    Parameters
    ----------
    term_text : str
        The examples term text (e.g., "Machine-readable output: examples:")
    is_subsection : bool
        If True, omit "Examples" suffix for cleaner nested titles.
    config : ExemplarConfig | None
        Optional configuration. If None, uses default ExemplarConfig().

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

    With custom configuration:

    >>> custom_config = ExemplarConfig(
    ...     examples_base_term="demos",
    ...     examples_term_suffix="demos",
    ...     examples_section_title="Demos",
    ... )
    >>> make_section_title("demos:", config=custom_config)
    'Demos'
    >>> make_section_title("Machine-readable output demos:", config=custom_config)
    'Machine-Readable Output Demos'
    """
    config = config or ExemplarConfig()
    base_term = config.examples_base_term
    term_suffix = config.examples_term_suffix
    section_title = config.examples_section_title

    # Remove trailing colon and normalize
    text = term_text.rstrip(":").strip()
    # Handle base term case (e.g., "examples:")
    if text.lower() == base_term:
        return section_title

    # Extract the prefix (category name) before the term suffix
    lower = text.lower()
    colon_suffix = f": {term_suffix}"
    space_suffix = f" {term_suffix}"
    if lower.endswith(colon_suffix):
        prefix = text[: -len(colon_suffix)]
    elif lower.endswith(space_suffix):
        prefix = text[: -len(space_suffix)]
    else:
        prefix = text

    # Title case the prefix
    titled_prefix = prefix.title()

    # For subsections, just use the prefix (cleaner nested titles)
    if is_subsection:
        return titled_prefix

    # For top-level sections, append the section title
    return f"{titled_prefix} {section_title}"


def _create_example_section(
    term_text: str,
    def_node: nodes.definition,
    *,
    is_subsection: bool = False,
    page_prefix: str = "",
    config: ExemplarConfig | None = None,
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
    page_prefix : str
        Optional prefix from the page name for unique section IDs.
    config : ExemplarConfig | None
        Optional configuration. If None, uses default ExemplarConfig().

    Returns
    -------
    nodes.section
        A section node with title and code blocks.
    """
    config = config or ExemplarConfig()
    section_id = make_section_id(
        term_text, is_subsection=is_subsection, page_prefix=page_prefix, config=config
    )
    section_title = make_section_title(
        term_text, is_subsection=is_subsection, config=config
    )

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
                text=f"{config.command_prefix}{line}",
                classes=list(config.code_classes),
            )
            code_block["language"] = config.code_language
            section += code_block

    return section


def transform_definition_list(
    dl_node: nodes.definition_list,
    *,
    page_prefix: str = "",
    config: ExemplarConfig | None = None,
) -> list[nodes.Node]:
    """Transform a definition list, converting examples items to code blocks.

    If there's a base "examples:" item followed by category-specific examples
    (e.g., "Field-scoped: examples:"), the categories are nested under the
    parent Examples section for cleaner ToC structure.

    Parameters
    ----------
    dl_node : nodes.definition_list
        A definition list node.
    page_prefix : str
        Optional prefix from the page name for unique section IDs.
    config : ExemplarConfig | None
        Optional configuration. If None, uses default ExemplarConfig().

    Returns
    -------
    list[nodes.Node]
        Transformed nodes - code blocks for examples, original for others.

    Note
    ----
    **Intentional reordering behavior:** This function always emits non-example
    items (preamble text, descriptions, etc.) before example sections, regardless
    of their original position in the definition list. This "flush first" approach
    groups conceptually related content: introductory material appears before
    examples, even if the source document interleaves them. This produces cleaner
    documentation structure where descriptions introduce their examples.

    If you need to preserve the original interleaved order, you would need to
    modify this function to track item positions during the first pass.
    """
    config = config or ExemplarConfig()

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

        if is_examples_term(term_text, config=config):
            if is_base_examples_term(term_text, config=config):
                base_examples_index = len(example_items)
            example_items.append((term_text, def_node))
        else:
            non_example_items.append(item)

    # Build result nodes
    result_nodes: list[nodes.Node] = []

    # Emit non-example items first (see docstring Note on reordering behavior)
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
            base_term,
            base_def,
            is_subsection=False,
            page_prefix=page_prefix,
            config=config,
        )

        # Add other examples as nested subsections
        for i, (term_text, def_node) in enumerate(example_items):
            if i == base_examples_index:
                continue  # Skip the base (already used as parent)
            subsection = _create_example_section(
                term_text,
                def_node,
                is_subsection=True,
                page_prefix=page_prefix,
                config=config,
            )
            parent_section += subsection

        result_nodes.append(parent_section)
    else:
        # No nesting - create flat sections (backwards compatible)
        for term_text, def_node in example_items:
            section = _create_example_section(
                term_text,
                def_node,
                is_subsection=False,
                page_prefix=page_prefix,
                config=config,
            )
            result_nodes.append(section)

    return result_nodes


def process_node(
    node: nodes.Node,
    *,
    page_prefix: str = "",
    config: ExemplarConfig | None = None,
) -> nodes.Node | list[nodes.Node]:
    """Process a node: strip ANSI codes and transform examples.

    Parameters
    ----------
    node : nodes.Node
        A docutils node to process.
    page_prefix : str
        Optional prefix from the page name for unique section IDs.
    config : ExemplarConfig | None
        Optional configuration. If None, uses default ExemplarConfig().

    Returns
    -------
    nodes.Node | list[nodes.Node]
        The processed node(s).
    """
    config = config or ExemplarConfig()

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
                        strip_ansi(child.astext()), config=config
                    ):
                        has_examples = True
                        break
            if has_examples:
                break

        if has_examples:
            return transform_definition_list(
                node, page_prefix=page_prefix, config=config
            )

    # Handle literal_block nodes - strip ANSI and apply usage highlighting
    if isinstance(node, nodes.literal_block):
        text = strip_ansi(node.astext())
        needs_update = text != node.astext()

        # Check if this is a usage block (starts with configured pattern)
        is_usage = text.lstrip().lower().startswith(config.usage_pattern.lower())

        if needs_update or is_usage:
            new_block = nodes.literal_block(text=text)
            # Preserve attributes
            for attr in ("language", "classes"):
                if attr in node:
                    new_block[attr] = node[attr]
            # Apply configured language to usage blocks
            if is_usage:
                new_block["language"] = config.usage_code_language
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
                result = process_node(child, page_prefix=page_prefix, config=config)
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
            result = process_node(child, page_prefix=page_prefix, config=config)
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


def _is_usage_block(node: nodes.Node, *, config: ExemplarConfig | None = None) -> bool:
    """Check if a node is a usage literal block.

    Parameters
    ----------
    node : nodes.Node
        A docutils node to check.
    config : ExemplarConfig | None
        Optional configuration. If None, uses default ExemplarConfig().

    Returns
    -------
    bool
        True if this is a usage block (literal_block starting with usage pattern).

    Examples
    --------
    >>> from docutils import nodes
    >>> _is_usage_block(nodes.literal_block(text="usage: cmd [-h]"))
    True
    >>> _is_usage_block(nodes.literal_block(text="Usage: myapp sync"))
    True
    >>> _is_usage_block(nodes.literal_block(text="  usage: cmd"))
    True
    >>> _is_usage_block(nodes.literal_block(text="some other text"))
    False
    >>> _is_usage_block(nodes.paragraph(text="usage: cmd"))
    False
    >>> _is_usage_block(nodes.section())
    False

    With custom configuration:

    >>> custom_config = ExemplarConfig(usage_pattern="synopsis:")
    >>> _is_usage_block(nodes.literal_block(text="synopsis: cmd"), config=custom_config)
    True
    >>> _is_usage_block(nodes.literal_block(text="usage: cmd"), config=custom_config)
    False
    """
    config = config or ExemplarConfig()
    if not isinstance(node, nodes.literal_block):
        return False
    text = node.astext()
    return text.lstrip().lower().startswith(config.usage_pattern.lower())


def _is_usage_section(node: nodes.Node) -> bool:
    """Check if a node is a usage section.

    Parameters
    ----------
    node : nodes.Node
        A docutils node to check.

    Returns
    -------
    bool
        True if this is a section with "usage" in its ID.

    Examples
    --------
    >>> from docutils import nodes
    >>> section = nodes.section()
    >>> section["ids"] = ["usage"]
    >>> _is_usage_section(section)
    True
    >>> section2 = nodes.section()
    >>> section2["ids"] = ["sync-usage"]
    >>> _is_usage_section(section2)
    True
    >>> section3 = nodes.section()
    >>> section3["ids"] = ["options"]
    >>> _is_usage_section(section3)
    False
    >>> _is_usage_section(nodes.paragraph())
    False
    """
    if not isinstance(node, nodes.section):
        return False
    ids: list[str] = node.get("ids", [])
    return any(id_str == "usage" or id_str.endswith("-usage") for id_str in ids)


def _is_examples_section(
    node: nodes.Node, *, config: ExemplarConfig | None = None
) -> bool:
    """Check if a node is an examples section.

    Parameters
    ----------
    node : nodes.Node
        A docutils node to check.
    config : ExemplarConfig | None
        Optional configuration. If None, uses default ExemplarConfig().

    Returns
    -------
    bool
        True if this is an examples section (section with term suffix in its ID).

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

    With custom configuration:

    >>> custom_config = ExemplarConfig(examples_term_suffix="demos")
    >>> section = nodes.section()
    >>> section["ids"] = ["demos"]
    >>> _is_examples_section(section, config=custom_config)
    True
    >>> section2 = nodes.section()
    >>> section2["ids"] = ["examples"]
    >>> _is_examples_section(section2, config=custom_config)
    False
    """
    config = config or ExemplarConfig()
    if not isinstance(node, nodes.section):
        return False
    ids: list[str] = node.get("ids", [])
    return any(config.examples_term_suffix in id_str.lower() for id_str in ids)


def _reorder_nodes(
    processed: list[nodes.Node], *, config: ExemplarConfig | None = None
) -> list[nodes.Node]:
    """Reorder nodes so usage sections/blocks appear before examples sections.

    This ensures the CLI usage synopsis appears above examples in the
    documentation, making it easier to understand command syntax before
    seeing example invocations.

    The function handles both:
    - Usage as literal_block (legacy format from older renderer)
    - Usage as section#usage (new format with TOC support)

    Parameters
    ----------
    processed : list[nodes.Node]
        List of processed docutils nodes.
    config : ExemplarConfig | None
        Optional configuration. If None, uses default ExemplarConfig().

    Returns
    -------
    list[nodes.Node]
        Reordered nodes with usage before examples (if enabled).

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

    Usage sections (with TOC heading) are also handled:

    >>> usage_section = nodes.section()
    >>> usage_section["ids"] = ["usage"]
    >>> result = _reorder_nodes([desc, examples, usage_section, args])
    >>> [n.get("ids", []) for n in result if isinstance(n, nodes.section)]
    [['usage'], ['examples'], ['arguments']]

    Reordering can be disabled via config:

    >>> no_reorder_config = ExemplarConfig(reorder_usage_before_examples=False)
    >>> result = _reorder_nodes([desc, examples, usage, args], config=no_reorder_config)
    >>> [type(n).__name__ for n in result]
    ['paragraph', 'section', 'literal_block', 'section']
    """
    config = config or ExemplarConfig()

    # If reordering is disabled, return as-is
    if not config.reorder_usage_before_examples:
        return processed

    # First pass: check if there are any examples sections
    has_examples = any(_is_examples_section(node, config=config) for node in processed)
    if not has_examples:
        # No examples, preserve original order
        return processed

    usage_nodes: list[nodes.Node] = []
    examples_sections: list[nodes.Node] = []
    other_before_examples: list[nodes.Node] = []
    other_after_examples: list[nodes.Node] = []

    seen_examples = False
    for node in processed:
        # Check for both usage block (literal_block) and usage section
        if _is_usage_block(node, config=config) or _is_usage_section(node):
            usage_nodes.append(node)
        elif _is_examples_section(node, config=config):
            examples_sections.append(node)
            seen_examples = True
        elif not seen_examples:
            other_before_examples.append(node)
        else:
            other_after_examples.append(node)

    # Order: before_examples → usage → examples → after_examples
    return (
        other_before_examples + usage_nodes + examples_sections + other_after_examples
    )


def _extract_sections_from_container(
    container: nodes.Node,
) -> tuple[nodes.Node, list[nodes.section]]:
    """Extract section nodes from a container, returning modified container.

    This function finds any section nodes that are children of the container
    (typically argparse_program), removes them from the container, and returns
    them separately so they can be made siblings.

    This is needed because Sphinx's TocTreeCollector only discovers sections
    that are direct children of the document or properly nested in the section
    hierarchy - sections inside arbitrary div containers are invisible to TOC.

    Parameters
    ----------
    container : nodes.Node
        A container node (typically argparse_program) that may contain sections.

    Returns
    -------
    tuple[nodes.Node, list[nodes.section]]
        A tuple of (modified_container, extracted_sections).

    Examples
    --------
    >>> from docutils import nodes
    >>> from sphinx_argparse_neo.nodes import argparse_program
    >>> container = argparse_program()
    >>> para = nodes.paragraph(text="Description")
    >>> examples = nodes.section()
    >>> examples["ids"] = ["examples"]
    >>> container += para
    >>> container += examples
    >>> modified, extracted = _extract_sections_from_container(container)
    >>> len(modified.children)
    1
    >>> len(extracted)
    1
    >>> extracted[0]["ids"]
    ['examples']
    """
    if not hasattr(container, "children"):
        return container, []

    extracted_sections: list[nodes.section] = []
    remaining_children: list[nodes.Node] = []

    for child in container.children:
        if isinstance(child, nodes.section):
            extracted_sections.append(child)
        else:
            remaining_children.append(child)

    # Update container with remaining children only
    container.children = remaining_children

    return container, extracted_sections


class CleanArgParseDirective(ArgparseDirective):  # type: ignore[misc]
    """ArgParse directive that strips ANSI codes and formats examples."""

    def run(self) -> list[nodes.Node]:
        """Run the directive, clean output, format examples, and reorder.

        The processing pipeline:
        1. Run base directive to get initial nodes
        2. Load configuration from Sphinx config
        3. Process each node (strip ANSI, transform examples definition lists)
        4. Extract sections from inside argparse_program containers
        5. Reorder so usage appears before examples (if enabled)
        """
        result = super().run()

        # Load configuration from Sphinx
        config = ExemplarConfig.from_sphinx_config(self.env.config)

        # Extract page name for unique section IDs across different CLI pages
        page_prefix = ""
        if hasattr(self.state, "document"):
            settings = self.state.document.settings
            if hasattr(settings, "env") and hasattr(settings.env, "docname"):
                # docname is like "cli/sync" - extract "sync"
                docname = settings.env.docname
                page_prefix = docname.split("/")[-1]

        processed: list[nodes.Node] = []
        for node in result:
            processed_node = process_node(node, page_prefix=page_prefix, config=config)
            if isinstance(processed_node, list):
                processed.extend(processed_node)
            else:
                processed.append(processed_node)

        # Extract sections from inside argparse_program containers
        # This is needed because sections inside divs are invisible to Sphinx TOC
        flattened: list[nodes.Node] = []
        for node in processed:
            # Check if this is an argparse_program (or similar container)
            # that might have sections inside
            node_class_name = type(node).__name__
            if node_class_name == "argparse_program":
                modified, extracted = _extract_sections_from_container(node)
                flattened.append(modified)
                flattened.extend(extracted)
            else:
                flattened.append(node)

        # Reorder: usage sections/blocks before examples sections
        return _reorder_nodes(flattened, config=config)


def setup(app: Sphinx) -> dict[str, t.Any]:
    """Register the clean argparse directive, lexers, and CLI roles.

    Configuration Options
    ---------------------
    The following configuration options can be set in conf.py:

    ``argparse_examples_term_suffix`` : str (default: "examples")
        Term must end with this string to be treated as examples header.

    ``argparse_examples_base_term`` : str (default: "examples")
        Exact match for the base examples section.

    ``argparse_examples_section_title`` : str (default: "Examples")
        Title used for the base examples section.

    ``argparse_usage_pattern`` : str (default: "usage:")
        Text must start with this to be treated as a usage block.

    ``argparse_examples_command_prefix`` : str (default: "$ ")
        Prefix added to each command line in examples code blocks.

    ``argparse_examples_code_language`` : str (default: "console")
        Language identifier for examples code blocks.

    ``argparse_examples_code_classes`` : list[str] (default: ["highlight-console"])
        CSS classes added to examples code blocks.

    ``argparse_usage_code_language`` : str (default: "cli-usage")
        Language identifier for usage blocks.

    ``argparse_reorder_usage_before_examples`` : bool (default: True)
        Whether to reorder nodes so usage appears before examples.

    Parameters
    ----------
    app : Sphinx
        The Sphinx application object.

    Returns
    -------
    dict
        Extension metadata.
    """
    # Load the base sphinx_argparse_neo extension first
    app.setup_extension("sphinx_argparse_neo")

    # Register configuration options
    app.add_config_value("argparse_examples_term_suffix", "examples", "html")
    app.add_config_value("argparse_examples_base_term", "examples", "html")
    app.add_config_value("argparse_examples_section_title", "Examples", "html")
    app.add_config_value("argparse_usage_pattern", "usage:", "html")
    app.add_config_value("argparse_examples_command_prefix", "$ ", "html")
    app.add_config_value("argparse_examples_code_language", "console", "html")
    app.add_config_value(
        "argparse_examples_code_classes", ["highlight-console"], "html"
    )
    app.add_config_value("argparse_usage_code_language", "cli-usage", "html")
    app.add_config_value("argparse_reorder_usage_before_examples", True, "html")

    # Override the argparse directive with our enhanced version
    app.add_directive("argparse", CleanArgParseDirective, override=True)

    # Register CLI usage lexer for usage block highlighting
    from cli_usage_lexer import CLIUsageLexer

    app.add_lexer("cli-usage", CLIUsageLexer)

    # Register argparse lexers for help output highlighting
    from argparse_lexer import (
        ArgparseHelpLexer,
        ArgparseLexer,
        ArgparseUsageLexer,
    )

    app.add_lexer("argparse", ArgparseLexer)
    app.add_lexer("argparse-usage", ArgparseUsageLexer)
    app.add_lexer("argparse-help", ArgparseHelpLexer)

    # Register CLI inline roles for documentation
    from argparse_roles import register_roles

    register_roles()

    return {"version": "4.0", "parallel_read_safe": True}
