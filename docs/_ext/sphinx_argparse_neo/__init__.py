"""sphinx_argparse_neo - Modern sphinx-argparse replacement.

A Sphinx extension for documenting argparse-based CLI tools that:
- Works with Sphinx 8.x AND 9.x (no autodoc.mock dependency)
- Fixes long-standing sphinx-argparse issues (TOC pollution, heading levels)
- Provides configurable output (rubrics vs sections, flattened subcommands)
- Supports extensibility via renderer classes
- Text processing utilities (ANSI stripping)
"""

from __future__ import annotations

import typing as t

from sphinx_argparse_neo.directive import ArgparseDirective
from sphinx_argparse_neo.nodes import (
    argparse_argument,
    argparse_group,
    argparse_program,
    argparse_subcommand,
    argparse_subcommands,
    argparse_usage,
    depart_argparse_argument_html,
    depart_argparse_group_html,
    depart_argparse_program_html,
    depart_argparse_subcommand_html,
    depart_argparse_subcommands_html,
    depart_argparse_usage_html,
    visit_argparse_argument_html,
    visit_argparse_group_html,
    visit_argparse_program_html,
    visit_argparse_subcommand_html,
    visit_argparse_subcommands_html,
    visit_argparse_usage_html,
)
from sphinx_argparse_neo.utils import strip_ansi

__all__ = [
    "ArgparseDirective",
    "strip_ansi",
]

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx

__version__ = "1.0.0"


def setup(app: Sphinx) -> dict[str, t.Any]:
    """Register the argparse directive and configuration options.

    Parameters
    ----------
    app : Sphinx
        The Sphinx application object.

    Returns
    -------
    dict[str, t.Any]
        Extension metadata.
    """
    # Configuration options
    app.add_config_value("argparse_group_title_prefix", "", "html")
    app.add_config_value("argparse_show_defaults", True, "html")
    app.add_config_value("argparse_show_choices", True, "html")
    app.add_config_value("argparse_show_types", True, "html")

    # Register custom nodes
    app.add_node(
        argparse_program,
        html=(visit_argparse_program_html, depart_argparse_program_html),
    )
    app.add_node(
        argparse_usage,
        html=(visit_argparse_usage_html, depart_argparse_usage_html),
    )
    app.add_node(
        argparse_group,
        html=(visit_argparse_group_html, depart_argparse_group_html),
    )
    app.add_node(
        argparse_argument,
        html=(visit_argparse_argument_html, depart_argparse_argument_html),
    )
    app.add_node(
        argparse_subcommands,
        html=(visit_argparse_subcommands_html, depart_argparse_subcommands_html),
    )
    app.add_node(
        argparse_subcommand,
        html=(visit_argparse_subcommand_html, depart_argparse_subcommand_html),
    )

    # Register directive
    app.add_directive("argparse", ArgparseDirective)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
