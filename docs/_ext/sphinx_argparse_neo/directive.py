"""Sphinx directive for argparse documentation.

This module provides the ArgparseDirective class that integrates
with Sphinx to generate documentation from ArgumentParser instances.
"""

from __future__ import annotations

import typing as t

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx_argparse_neo.compat import get_parser_from_module
from sphinx_argparse_neo.parser import extract_parser
from sphinx_argparse_neo.renderer import ArgparseRenderer, RenderConfig

if t.TYPE_CHECKING:
    import argparse


class ArgparseDirective(SphinxDirective):
    """Sphinx directive for documenting argparse-based CLI tools.

    Usage
    -----
    .. argparse::
       :module: myapp.cli
       :func: create_parser
       :prog: myapp

    Options
    -------
    :module:
        The Python module containing the parser factory function.
    :func:
        The function name that returns an ArgumentParser.
        Can be a dotted path like "Class.method".
    :prog:
        Override the program name (optional).
    :path:
        Navigate to a specific subparser by path (e.g., "sync pull").
    :no-defaults:
        Don't show default values (flag).
    :no-description:
        Don't show parser description (flag).
    :no-epilog:
        Don't show parser epilog (flag).
    :mock-modules:
        Comma-separated list of modules to mock during import.

    Examples
    --------
    In RST documentation::

        .. argparse::
           :module: myapp.cli
           :func: create_parser
           :prog: myapp

           :path: subcommand
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0

    option_spec: t.ClassVar[dict[str, t.Any]] = {
        "module": directives.unchanged_required,
        "func": directives.unchanged_required,
        "prog": directives.unchanged,
        "path": directives.unchanged,
        "no-defaults": directives.flag,
        "no-description": directives.flag,
        "no-epilog": directives.flag,
        "no-choices": directives.flag,
        "no-types": directives.flag,
        "mock-modules": directives.unchanged,
        # sphinx-argparse compatibility options
        "nosubcommands": directives.flag,
        "nodefault": directives.flag,
        "noepilog": directives.flag,
        "nodescription": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive and return docutils nodes.

        Returns
        -------
        list[nodes.Node]
            List of docutils nodes representing the CLI documentation.
        """
        # Get required options
        module_name = self.options.get("module")
        func_name = self.options.get("func")

        if not module_name or not func_name:
            error = self.state_machine.reporter.error(
                "argparse directive requires :module: and :func: options",
                line=self.lineno,
            )
            return [error]

        # Parse mock modules
        mock_modules: list[str] | None = None
        if "mock-modules" in self.options:
            mock_modules = [m.strip() for m in self.options["mock-modules"].split(",")]

        # Load the parser
        try:
            parser = get_parser_from_module(module_name, func_name, mock_modules)
        except Exception as e:
            error = self.state_machine.reporter.error(
                f"Failed to load parser from {module_name}:{func_name}: {e}",
                line=self.lineno,
            )
            return [error]

        # Override prog if specified
        if "prog" in self.options:
            parser.prog = self.options["prog"]

        # Navigate to subparser if path specified
        if "path" in self.options:
            parser = self._navigate_to_subparser(parser, self.options["path"])
            if parser is None:
                error = self.state_machine.reporter.error(
                    f"Subparser path not found: {self.options['path']}",
                    line=self.lineno,
                )
                return [error]

        # Build render config from directive options and Sphinx config
        config = self._build_render_config()

        # Extract parser info
        parser_info = extract_parser(parser)

        # Apply directive-level overrides
        # Handle both new-style and sphinx-argparse compatibility options
        if "no-description" in self.options or "nodescription" in self.options:
            parser_info = parser_info.__class__(
                prog=parser_info.prog,
                usage=parser_info.usage,
                bare_usage=parser_info.bare_usage,
                description=None,
                epilog=parser_info.epilog,
                argument_groups=parser_info.argument_groups,
                subcommands=parser_info.subcommands,
                subcommand_dest=parser_info.subcommand_dest,
            )
        if "no-epilog" in self.options or "noepilog" in self.options:
            parser_info = parser_info.__class__(
                prog=parser_info.prog,
                usage=parser_info.usage,
                bare_usage=parser_info.bare_usage,
                description=parser_info.description,
                epilog=None,
                argument_groups=parser_info.argument_groups,
                subcommands=parser_info.subcommands,
                subcommand_dest=parser_info.subcommand_dest,
            )
        if "nosubcommands" in self.options:
            parser_info = parser_info.__class__(
                prog=parser_info.prog,
                usage=parser_info.usage,
                bare_usage=parser_info.bare_usage,
                description=parser_info.description,
                epilog=parser_info.epilog,
                argument_groups=parser_info.argument_groups,
                subcommands=None,
                subcommand_dest=None,
            )

        # Render to nodes
        renderer = ArgparseRenderer(config=config, state=self.state)
        return t.cast(list[nodes.Node], renderer.render(parser_info))

    def _build_render_config(self) -> RenderConfig:
        """Build RenderConfig from directive and Sphinx config options.

        Returns
        -------
        RenderConfig
            Configuration for the renderer.
        """
        # Start with Sphinx config defaults
        config = RenderConfig.from_sphinx_config(self.config)

        # Override with directive options
        # Handle both new-style and sphinx-argparse compatibility options
        if "no-defaults" in self.options or "nodefault" in self.options:
            config.show_defaults = False
        if "no-choices" in self.options:
            config.show_choices = False
        if "no-types" in self.options:
            config.show_types = False

        return config

    def _navigate_to_subparser(
        self, parser: argparse.ArgumentParser, path: str
    ) -> argparse.ArgumentParser | None:
        """Navigate to a nested subparser by path.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            The root parser.
        path : str
            Space-separated path to the subparser (e.g., "sync pull").

        Returns
        -------
        argparse.ArgumentParser | None
            The subparser, or None if not found.
        """
        import argparse as argparse_module

        current = parser
        for name in path.split():
            # Find subparsers action
            subparser_action = None
            for action in current._actions:
                if isinstance(action, argparse_module._SubParsersAction):
                    subparser_action = action
                    break

            if subparser_action is None:
                return None

            # Find the named subparser
            choices = subparser_action.choices or {}
            if name not in choices:
                return None

            current = choices[name]

        return current
