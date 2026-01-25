"""Renderer - convert ParserInfo to docutils nodes.

This module provides the ArgparseRenderer class that transforms
structured parser information into docutils nodes for documentation.
"""

from __future__ import annotations

import dataclasses
import typing as t

from docutils import nodes
from docutils.statemachine import StringList
from sphinx_argparse_neo.nodes import (
    argparse_argument,
    argparse_group,
    argparse_program,
    argparse_subcommand,
    argparse_subcommands,
    argparse_usage,
)
from sphinx_argparse_neo.parser import (
    ArgumentGroup,
    ArgumentInfo,
    MutuallyExclusiveGroup,
    ParserInfo,
    SubcommandInfo,
)
from sphinx_argparse_neo.utils import escape_rst_emphasis

if t.TYPE_CHECKING:
    from docutils.parsers.rst.states import RSTState
    from sphinx.config import Config


@dataclasses.dataclass
class RenderConfig:
    """Configuration for the renderer.

    Examples
    --------
    >>> config = RenderConfig()
    >>> config.show_defaults
    True
    >>> config.group_title_prefix
    ''
    """

    group_title_prefix: str = ""
    show_defaults: bool = True
    show_choices: bool = True
    show_types: bool = True

    @classmethod
    def from_sphinx_config(cls, config: Config) -> RenderConfig:
        """Create RenderConfig from Sphinx configuration.

        Parameters
        ----------
        config : Config
            Sphinx configuration object.

        Returns
        -------
        RenderConfig
            Render configuration based on Sphinx config values.
        """
        return cls(
            group_title_prefix=getattr(config, "argparse_group_title_prefix", ""),
            show_defaults=getattr(config, "argparse_show_defaults", True),
            show_choices=getattr(config, "argparse_show_choices", True),
            show_types=getattr(config, "argparse_show_types", True),
        )


class ArgparseRenderer:
    """Render ParserInfo to docutils nodes.

    This class can be subclassed to customize rendering behavior.
    Override individual methods to change how specific elements are rendered.

    Parameters
    ----------
    config : RenderConfig
        Rendering configuration.
    state : RSTState | None
        RST state for parsing nested RST content.

    Examples
    --------
    >>> from sphinx_argparse_neo.parser import ParserInfo
    >>> config = RenderConfig()
    >>> renderer = ArgparseRenderer(config)
    >>> info = ParserInfo(
    ...     prog="myapp",
    ...     usage=None,
    ...     bare_usage="myapp [-h]",
    ...     description="My app",
    ...     epilog=None,
    ...     argument_groups=[],
    ...     subcommands=None,
    ...     subcommand_dest=None,
    ... )
    >>> result = renderer.render(info)
    >>> isinstance(result, list)
    True
    """

    def __init__(
        self,
        config: RenderConfig | None = None,
        state: RSTState | None = None,
    ) -> None:
        """Initialize the renderer."""
        self.config = config or RenderConfig()
        self.state = state

    @staticmethod
    def _extract_id_prefix(prog: str) -> str:
        """Extract subcommand from prog for unique section IDs.

        Parameters
        ----------
        prog : str
            The program name, potentially with subcommand (e.g., "tmuxp load").

        Returns
        -------
        str
            The subcommand part for use as ID prefix, or empty string if none.

        Examples
        --------
        >>> ArgparseRenderer._extract_id_prefix("tmuxp load")
        'load'
        >>> ArgparseRenderer._extract_id_prefix("tmuxp")
        ''
        >>> ArgparseRenderer._extract_id_prefix("vcspull sync")
        'sync'
        >>> ArgparseRenderer._extract_id_prefix("myapp sub cmd")
        'sub-cmd'
        """
        parts = prog.split()
        if len(parts) <= 1:
            return ""
        # Join remaining parts with hyphen for multi-level subcommands
        return "-".join(parts[1:])

    def render(self, parser_info: ParserInfo) -> list[nodes.Node]:
        """Render a complete parser to docutils nodes.

        Parameters
        ----------
        parser_info : ParserInfo
            The parsed parser information.

        Returns
        -------
        list[nodes.Node]
            List of docutils nodes representing the documentation.

        Note
        ----
        Sections for Usage and argument groups are emitted as siblings of
        argparse_program rather than children. This allows Sphinx's
        TocTreeCollector to discover them for inclusion in the table of
        contents.

        The rendered structure is:

        - argparse_program (description only, no "examples:" part)
        - section#usage (h3 "Usage" with usage block)
        - section#positional-arguments (h3)
        - section#options (h3)

        The "examples:" definition list in descriptions is left for
        argparse_exemplar.py to transform into a proper Examples section.
        """
        result: list[nodes.Node] = []

        # Create program container for description only
        program_node = argparse_program()
        program_node["prog"] = parser_info.prog

        # Add description (may contain "examples:" definition list for later
        # transformation by argparse_exemplar.py)
        if parser_info.description:
            desc_nodes = self._parse_text(parser_info.description)
            program_node.extend(desc_nodes)

        result.append(program_node)

        # Extract ID prefix from prog for unique section IDs
        # e.g., "tmuxp load" -> "load", "myapp" -> ""
        id_prefix = self._extract_id_prefix(parser_info.prog)

        # Add Usage section as sibling (for TOC visibility)
        usage_section = self.render_usage_section(parser_info, id_prefix=id_prefix)
        result.append(usage_section)

        # Add argument groups as sibling sections (for TOC visibility)
        for group in parser_info.argument_groups:
            group_section = self.render_group_section(group, id_prefix=id_prefix)
            result.append(group_section)

        # Add subcommands
        if parser_info.subcommands:
            subcommands_node = self.render_subcommands(parser_info.subcommands)
            result.append(subcommands_node)

        # Add epilog
        if parser_info.epilog:
            epilog_nodes = self._parse_text(parser_info.epilog)
            result.extend(epilog_nodes)

        return self.post_process(result)

    def render_usage(self, parser_info: ParserInfo) -> argparse_usage:
        """Render the usage block.

        Parameters
        ----------
        parser_info : ParserInfo
            The parser information.

        Returns
        -------
        argparse_usage
            Usage node.
        """
        usage_node = argparse_usage()
        usage_node["usage"] = parser_info.bare_usage
        return usage_node

    def render_usage_section(
        self, parser_info: ParserInfo, *, id_prefix: str = ""
    ) -> nodes.section:
        """Render usage as a section with heading for TOC visibility.

        Creates a proper section node with "Usage" heading containing the
        usage block. This structure allows Sphinx's TocTreeCollector to
        discover it for the table of contents.

        Parameters
        ----------
        parser_info : ParserInfo
            The parser information.
        id_prefix : str
            Optional prefix for the section ID (e.g., "load" -> "load-usage").
            Used to ensure unique IDs when multiple argparse directives exist
            on the same page.

        Returns
        -------
        nodes.section
            Section node containing the usage block with a "Usage" heading.

        Examples
        --------
        >>> from sphinx_argparse_neo.parser import ParserInfo
        >>> renderer = ArgparseRenderer()
        >>> info = ParserInfo(
        ...     prog="myapp",
        ...     usage=None,
        ...     bare_usage="myapp [-h] command",
        ...     description=None,
        ...     epilog=None,
        ...     argument_groups=[],
        ...     subcommands=None,
        ...     subcommand_dest=None,
        ... )
        >>> section = renderer.render_usage_section(info)
        >>> section["ids"]
        ['usage']

        With prefix for subcommand pages:

        >>> section = renderer.render_usage_section(info, id_prefix="load")
        >>> section["ids"]
        ['load-usage']
        >>> section.children[0].astext()
        'Usage'
        """
        section_id = f"{id_prefix}-usage" if id_prefix else "usage"
        section = nodes.section()
        section["ids"] = [section_id]
        section["names"] = [nodes.fully_normalize_name("Usage")]
        section += nodes.title("Usage", "Usage")

        usage_node = argparse_usage()
        usage_node["usage"] = parser_info.bare_usage
        section += usage_node

        return section

    def render_group_section(
        self, group: ArgumentGroup, *, id_prefix: str = ""
    ) -> nodes.section:
        """Render an argument group wrapped in a section for TOC visibility.

        Creates a proper section node with the group title as heading,
        containing the argparse_group node. This structure allows Sphinx's
        TocTreeCollector to discover it for the table of contents.

        Parameters
        ----------
        group : ArgumentGroup
            The argument group to render.
        id_prefix : str
            Optional prefix for the section ID (e.g., "load" -> "load-options").
            Used to ensure unique IDs when multiple argparse directives exist
            on the same page.

        Returns
        -------
        nodes.section
            Section node containing the group for TOC discovery.

        Examples
        --------
        >>> from sphinx_argparse_neo.parser import ArgumentGroup
        >>> renderer = ArgparseRenderer()
        >>> group = ArgumentGroup(
        ...     title="positional arguments",
        ...     description=None,
        ...     arguments=[],
        ...     mutually_exclusive=[],
        ... )
        >>> section = renderer.render_group_section(group)
        >>> section["ids"]
        ['positional-arguments']

        With prefix for subcommand pages:

        >>> section = renderer.render_group_section(group, id_prefix="load")
        >>> section["ids"]
        ['load-positional-arguments']
        >>> section.children[0].astext()
        'Positional Arguments'
        """
        # Title case the group title for proper display
        raw_title = group.title or "Arguments"
        title = raw_title.title()  # "positional arguments" -> "Positional Arguments"

        if self.config.group_title_prefix:
            title = f"{self.config.group_title_prefix}{title}"

        # Generate section ID from title (with optional prefix for uniqueness)
        base_id = title.lower().replace(" ", "-")
        section_id = f"{id_prefix}-{base_id}" if id_prefix else base_id

        # Create section wrapper for TOC discovery
        section = nodes.section()
        section["ids"] = [section_id]
        section["names"] = [nodes.fully_normalize_name(title)]

        # Add title for TOC - Sphinx's TocTreeCollector looks for this
        section += nodes.title(title, title)

        # Create the styled group container (with empty title - section provides it)
        # Pass id_prefix to render_group so arguments get unique IDs
        group_node = self.render_group(group, include_title=False, id_prefix=id_prefix)
        section += group_node

        return section

    def render_group(
        self,
        group: ArgumentGroup,
        include_title: bool = True,
        *,
        id_prefix: str = "",
    ) -> argparse_group:
        """Render an argument group.

        Parameters
        ----------
        group : ArgumentGroup
            The argument group to render.
        include_title : bool
            Whether to include the title in the group node. When False,
            the title is assumed to come from a parent section node.
            Default is True for backwards compatibility.
        id_prefix : str
            Optional prefix for argument IDs (e.g., "shell" -> "shell-h").
            Used to ensure unique IDs when multiple argparse directives exist
            on the same page.

        Returns
        -------
        argparse_group
            Group node containing argument nodes.
        """
        group_node = argparse_group()

        if include_title:
            title = group.title
            if self.config.group_title_prefix:
                title = f"{self.config.group_title_prefix}{title}"
            group_node["title"] = title
        else:
            # Title provided by parent section
            group_node["title"] = ""

        group_node["description"] = group.description

        # Add individual arguments
        for arg in group.arguments:
            arg_node = self.render_argument(arg, id_prefix=id_prefix)
            group_node.append(arg_node)

        # Add mutually exclusive groups
        for mutex in group.mutually_exclusive:
            mutex_nodes = self.render_mutex_group(mutex, id_prefix=id_prefix)
            group_node.extend(mutex_nodes)

        return group_node

    def render_argument(
        self, arg: ArgumentInfo, *, id_prefix: str = ""
    ) -> argparse_argument:
        """Render a single argument.

        Parameters
        ----------
        arg : ArgumentInfo
            The argument to render.
        id_prefix : str
            Optional prefix for the argument ID (e.g., "shell" -> "shell-L").
            Used to ensure unique IDs when multiple argparse directives exist
            on the same page.

        Returns
        -------
        argparse_argument
            Argument node.
        """
        arg_node = argparse_argument()
        arg_node["names"] = arg.names
        arg_node["help"] = arg.help
        arg_node["metavar"] = arg.metavar
        arg_node["required"] = arg.required
        arg_node["id_prefix"] = id_prefix

        if self.config.show_defaults:
            arg_node["default_string"] = arg.default_string

        if self.config.show_choices:
            arg_node["choices"] = arg.choices

        if self.config.show_types:
            arg_node["type_name"] = arg.type_name

        return arg_node

    def render_mutex_group(
        self, mutex: MutuallyExclusiveGroup, *, id_prefix: str = ""
    ) -> list[argparse_argument]:
        """Render a mutually exclusive group.

        Parameters
        ----------
        mutex : MutuallyExclusiveGroup
            The mutually exclusive group.
        id_prefix : str
            Optional prefix for argument IDs (e.g., "shell" -> "shell-h").

        Returns
        -------
        list[argparse_argument]
            List of argument nodes with mutex indicator.
        """
        result: list[argparse_argument] = []
        for arg in mutex.arguments:
            arg_node = self.render_argument(arg, id_prefix=id_prefix)
            # Mark as part of mutex group
            arg_node["mutex"] = True
            arg_node["mutex_required"] = mutex.required
            result.append(arg_node)
        return result

    def render_subcommands(
        self, subcommands: list[SubcommandInfo]
    ) -> argparse_subcommands:
        """Render subcommands section.

        Parameters
        ----------
        subcommands : list[SubcommandInfo]
            List of subcommand information.

        Returns
        -------
        argparse_subcommands
            Subcommands container node.
        """
        container = argparse_subcommands()
        container["title"] = "Sub-commands"

        for subcmd in subcommands:
            subcmd_node = self.render_subcommand(subcmd)
            container.append(subcmd_node)

        return container

    def render_subcommand(self, subcmd: SubcommandInfo) -> argparse_subcommand:
        """Render a single subcommand.

        Parameters
        ----------
        subcmd : SubcommandInfo
            The subcommand information.

        Returns
        -------
        argparse_subcommand
            Subcommand node, potentially containing nested parser content.
        """
        subcmd_node = argparse_subcommand()
        subcmd_node["name"] = subcmd.name
        subcmd_node["aliases"] = subcmd.aliases
        subcmd_node["help"] = subcmd.help

        # Recursively render the subcommand's parser
        if subcmd.parser:
            nested_nodes = self.render(subcmd.parser)
            subcmd_node.extend(nested_nodes)

        return subcmd_node

    def post_process(self, result_nodes: list[nodes.Node]) -> list[nodes.Node]:
        """Post-process the rendered nodes.

        Override this method to apply transformations after rendering.

        Parameters
        ----------
        result_nodes : list[nodes.Node]
            The rendered nodes.

        Returns
        -------
        list[nodes.Node]
            Post-processed nodes.
        """
        return result_nodes

    def _parse_text(self, text: str) -> list[nodes.Node]:
        """Parse text as RST or MyST content.

        Parameters
        ----------
        text : str
            Text to parse.

        Returns
        -------
        list[nodes.Node]
            Parsed docutils nodes.
        """
        if not text:
            return []

        # Escape RST emphasis patterns before parsing (e.g., "django-*" -> "django-\*")
        text = escape_rst_emphasis(text)

        if self.state is None:
            # No state machine available, return as paragraph
            para = nodes.paragraph(text=text)
            return [para]

        # Use the state machine to parse RST
        container = nodes.container()
        self.state.nested_parse(
            StringList(text.split("\n")),
            0,
            container,
        )
        return list(container.children)


def create_renderer(
    config: RenderConfig | None = None,
    state: RSTState | None = None,
    renderer_class: type[ArgparseRenderer] | None = None,
) -> ArgparseRenderer:
    """Create a renderer instance.

    Parameters
    ----------
    config : RenderConfig | None
        Rendering configuration.
    state : RSTState | None
        RST state for parsing.
    renderer_class : type[ArgparseRenderer] | None
        Custom renderer class to use.

    Returns
    -------
    ArgparseRenderer
        Configured renderer instance.
    """
    cls = renderer_class or ArgparseRenderer
    return cls(config=config, state=state)
