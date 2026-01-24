"""Tests for sphinx_argparse_neo.renderer module."""

from __future__ import annotations

import argparse
import typing as t

from docutils import nodes
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
    extract_parser,
)
from sphinx_argparse_neo.renderer import (
    ArgparseRenderer,
    RenderConfig,
    create_renderer,
)

# --- RenderConfig tests ---


def test_render_config_defaults() -> None:
    """Test RenderConfig default values."""
    config = RenderConfig()

    assert config.group_title_prefix == ""
    assert config.show_defaults is True
    assert config.show_choices is True
    assert config.show_types is True


def test_render_config_custom_values() -> None:
    """Test RenderConfig with custom values."""
    config = RenderConfig(
        group_title_prefix="CLI ",
        show_defaults=False,
        show_choices=False,
        show_types=False,
    )

    assert config.group_title_prefix == "CLI "
    assert config.show_defaults is False
    assert config.show_choices is False
    assert config.show_types is False


# --- ArgparseRenderer basic tests ---


def test_renderer_creation_default_config() -> None:
    """Test creating renderer with default config."""
    renderer = ArgparseRenderer()

    assert renderer.config is not None
    assert renderer.config.show_defaults is True


def test_renderer_creation_custom_config() -> None:
    """Test creating renderer with custom config."""
    config = RenderConfig(group_title_prefix="CLI ")
    renderer = ArgparseRenderer(config=config)

    assert renderer.config.group_title_prefix == "CLI "


def test_create_renderer_factory() -> None:
    """Test create_renderer factory function."""
    renderer = create_renderer()
    assert isinstance(renderer, ArgparseRenderer)


def test_create_renderer_with_config() -> None:
    """Test create_renderer with custom config."""
    config = RenderConfig(show_types=False)
    renderer = create_renderer(config=config)

    assert renderer.config.show_types is False


# --- Render method tests ---


def test_render_simple_parser(simple_parser: argparse.ArgumentParser) -> None:
    """Test rendering a simple parser produces sibling nodes for TOC.

    The renderer now outputs sections as siblings of argparse_program:
    - argparse_program (description only)
    - section#usage
    - section#positional-arguments
    - section#options
    """
    parser_info = extract_parser(simple_parser)
    renderer = ArgparseRenderer()
    rendered_nodes = renderer.render(parser_info)

    # Should have multiple nodes: program + usage section + group sections
    assert len(rendered_nodes) >= 3

    # First node is argparse_program
    assert isinstance(rendered_nodes[0], argparse_program)
    assert rendered_nodes[0]["prog"] == "myapp"

    # Second node should be usage section
    assert isinstance(rendered_nodes[1], nodes.section)
    assert "usage" in rendered_nodes[1]["ids"]


def test_render_includes_usage(simple_parser: argparse.ArgumentParser) -> None:
    """Test that render includes usage as a sibling section."""
    parser_info = extract_parser(simple_parser)
    renderer = ArgparseRenderer()
    rendered_nodes = renderer.render(parser_info)

    # Find the usage section (sibling of program, not child)
    usage_sections = [
        n
        for n in rendered_nodes
        if isinstance(n, nodes.section) and "usage" in n.get("ids", [])
    ]

    assert len(usage_sections) == 1

    # Usage section should contain argparse_usage node
    usage_section = usage_sections[0]
    usage_node = [c for c in usage_section.children if isinstance(c, argparse_usage)]
    assert len(usage_node) == 1
    assert "myapp" in usage_node[0]["usage"]


def test_render_includes_groups(simple_parser: argparse.ArgumentParser) -> None:
    """Test that render includes argument groups as sibling sections."""
    parser_info = extract_parser(simple_parser)
    renderer = ArgparseRenderer()
    rendered_nodes = renderer.render(parser_info)

    # Groups are now wrapped in sections and are siblings of program
    # Find sections that contain argparse_group nodes
    group_sections = [
        n
        for n in rendered_nodes
        if isinstance(n, nodes.section)
        and any(isinstance(c, argparse_group) for c in n.children)
    ]

    assert len(group_sections) >= 1


def test_render_groups_contain_arguments(
    simple_parser: argparse.ArgumentParser,
) -> None:
    """Test that rendered groups contain argument nodes."""
    parser_info = extract_parser(simple_parser)
    renderer = ArgparseRenderer()
    rendered_nodes = renderer.render(parser_info)

    # Find sections that contain argparse_group nodes
    group_sections = [
        n
        for n in rendered_nodes
        if isinstance(n, nodes.section)
        and any(isinstance(c, argparse_group) for c in n.children)
    ]

    # Collect all arguments from groups inside sections
    all_args: list[argparse_argument] = []
    for section in group_sections:
        for child in section.children:
            if isinstance(child, argparse_group):
                all_args.extend(
                    arg for arg in child.children if isinstance(arg, argparse_argument)
                )

    assert len(all_args) >= 1


def test_render_with_subcommands(
    parser_with_subcommands: argparse.ArgumentParser,
) -> None:
    """Test rendering parser with subcommands."""
    parser_info = extract_parser(parser_with_subcommands)
    renderer = ArgparseRenderer()
    rendered_nodes = renderer.render(parser_info)

    # Subcommands node is a sibling of program
    subcommands_nodes = [
        n for n in rendered_nodes if isinstance(n, argparse_subcommands)
    ]

    assert len(subcommands_nodes) == 1

    # Check subcommand children
    subs_container = subcommands_nodes[0]
    subcmd_nodes = [
        c for c in subs_container.children if isinstance(c, argparse_subcommand)
    ]
    assert len(subcmd_nodes) == 2


# --- Config option effect tests ---


def _collect_args_from_rendered_nodes(
    rendered_nodes: list[nodes.Node],
) -> list[argparse_argument]:
    """Collect all argparse_argument nodes from rendered output."""
    all_args: list[argparse_argument] = []
    for node in rendered_nodes:
        if isinstance(node, nodes.section):
            for child in node.children:
                if isinstance(child, argparse_group):
                    all_args.extend(
                        arg
                        for arg in child.children
                        if isinstance(arg, argparse_argument)
                    )
    return all_args


def test_render_group_title_prefix() -> None:
    """Test that group_title_prefix is applied to section titles."""
    parser = argparse.ArgumentParser(prog="test")
    parser.add_argument("--opt")
    parser_info = extract_parser(parser)

    config = RenderConfig(group_title_prefix="CLI: ")
    renderer = ArgparseRenderer(config=config)
    rendered_nodes = renderer.render(parser_info)

    # Find sections that contain argparse_group
    group_sections = [
        n
        for n in rendered_nodes
        if isinstance(n, nodes.section)
        and any(isinstance(c, argparse_group) for c in n.children)
    ]

    # Section IDs should include the prefix (normalized)
    ids = [section["ids"][0] for section in group_sections if section["ids"]]
    assert any("cli:" in id_str.lower() for id_str in ids)


def test_render_show_defaults_false() -> None:
    """Test that show_defaults=False hides defaults."""
    parser = argparse.ArgumentParser(prog="test")
    parser.add_argument("--opt", default="value")
    parser_info = extract_parser(parser)

    config = RenderConfig(show_defaults=False)
    renderer = ArgparseRenderer(config=config)
    rendered_nodes = renderer.render(parser_info)

    all_args = _collect_args_from_rendered_nodes(rendered_nodes)

    # Default string should not be set
    for arg in all_args:
        assert arg.get("default_string") is None


def test_render_show_choices_false() -> None:
    """Test that show_choices=False hides choices."""
    parser = argparse.ArgumentParser(prog="test")
    parser.add_argument("--format", choices=["json", "yaml"])
    parser_info = extract_parser(parser)

    config = RenderConfig(show_choices=False)
    renderer = ArgparseRenderer(config=config)
    rendered_nodes = renderer.render(parser_info)

    all_args = _collect_args_from_rendered_nodes(rendered_nodes)

    # Choices should not be set
    for arg in all_args:
        assert arg.get("choices") is None


def test_render_show_types_false() -> None:
    """Test that show_types=False hides type info."""
    parser = argparse.ArgumentParser(prog="test")
    parser.add_argument("--count", type=int)
    parser_info = extract_parser(parser)

    config = RenderConfig(show_types=False)
    renderer = ArgparseRenderer(config=config)
    rendered_nodes = renderer.render(parser_info)

    all_args = _collect_args_from_rendered_nodes(rendered_nodes)

    # Type name should not be set
    for arg in all_args:
        assert arg.get("type_name") is None


# --- Individual render method tests ---


def test_render_usage_method() -> None:
    """Test render_usage method directly."""
    parser_info = ParserInfo(
        prog="test",
        usage=None,
        bare_usage="test [-h] [-v]",
        description=None,
        epilog=None,
        argument_groups=[],
        subcommands=None,
        subcommand_dest=None,
    )

    renderer = ArgparseRenderer()
    usage_node = renderer.render_usage(parser_info)

    assert isinstance(usage_node, argparse_usage)
    assert usage_node["usage"] == "test [-h] [-v]"


def test_render_argument_method() -> None:
    """Test render_argument method directly."""
    arg_info = ArgumentInfo(
        names=["-v", "--verbose"],
        help="Enable verbose mode",
        default=False,
        default_string="False",
        choices=None,
        required=False,
        metavar=None,
        nargs=None,
        action="store_true",
        type_name=None,
        const=True,
        dest="verbose",
    )

    renderer = ArgparseRenderer()
    arg_node = renderer.render_argument(arg_info)

    assert isinstance(arg_node, argparse_argument)
    assert arg_node["names"] == ["-v", "--verbose"]
    assert arg_node["help"] == "Enable verbose mode"


def test_render_group_method() -> None:
    """Test render_group method directly."""
    group_info = ArgumentGroup(
        title="Options",
        description="Available options",
        arguments=[
            ArgumentInfo(
                names=["-v"],
                help="Verbose",
                default=False,
                default_string="False",
                choices=None,
                required=False,
                metavar=None,
                nargs=None,
                action="store_true",
                type_name=None,
                const=True,
                dest="verbose",
            ),
        ],
        mutually_exclusive=[],
    )

    renderer = ArgparseRenderer()
    group_node = renderer.render_group(group_info)

    assert isinstance(group_node, argparse_group)
    assert group_node["title"] == "Options"
    assert group_node["description"] == "Available options"
    assert len(group_node.children) == 1


def test_render_mutex_group_method() -> None:
    """Test render_mutex_group method."""
    mutex = MutuallyExclusiveGroup(
        arguments=[
            ArgumentInfo(
                names=["-v"],
                help="Verbose",
                default=False,
                default_string="False",
                choices=None,
                required=False,
                metavar=None,
                nargs=None,
                action="store_true",
                type_name=None,
                const=True,
                dest="verbose",
            ),
            ArgumentInfo(
                names=["-q"],
                help="Quiet",
                default=False,
                default_string="False",
                choices=None,
                required=False,
                metavar=None,
                nargs=None,
                action="store_true",
                type_name=None,
                const=True,
                dest="quiet",
            ),
        ],
        required=True,
    )

    renderer = ArgparseRenderer()
    nodes = renderer.render_mutex_group(mutex)

    assert len(nodes) == 2
    assert all(isinstance(n, argparse_argument) for n in nodes)
    assert all(n.get("mutex") is True for n in nodes)
    assert all(n.get("mutex_required") is True for n in nodes)


def test_render_subcommand_method() -> None:
    """Test render_subcommand method."""
    nested_parser = ParserInfo(
        prog="myapp sub",
        usage=None,
        bare_usage="myapp sub [-h]",
        description="Subcommand description",
        epilog=None,
        argument_groups=[],
        subcommands=None,
        subcommand_dest=None,
    )

    subcmd_info = SubcommandInfo(
        name="sub",
        aliases=["s"],
        help="Subcommand help",
        parser=nested_parser,
    )

    renderer = ArgparseRenderer()
    subcmd_node = renderer.render_subcommand(subcmd_info)

    assert isinstance(subcmd_node, argparse_subcommand)
    assert subcmd_node["name"] == "sub"
    assert subcmd_node["aliases"] == ["s"]
    assert subcmd_node["help"] == "Subcommand help"

    # Should have nested program
    nested = [c for c in subcmd_node.children if isinstance(c, argparse_program)]
    assert len(nested) == 1


# --- Post-process hook test ---


def test_post_process_default() -> None:
    """Test that default post_process returns nodes unchanged."""
    renderer = ArgparseRenderer()

    from docutils import nodes as dn

    input_nodes = [dn.paragraph(text="test")]

    result = renderer.post_process(input_nodes)

    assert result == input_nodes


def test_post_process_custom() -> None:
    """Test custom post_process implementation."""

    class CustomRenderer(ArgparseRenderer):  # type: ignore[misc]
        def post_process(self, result_nodes: list[t.Any]) -> list[t.Any]:
            # Add a marker to each node
            for node in result_nodes:
                node["custom_marker"] = True
            return result_nodes

    renderer = CustomRenderer()

    from docutils import nodes as dn

    input_nodes = [dn.paragraph(text="test")]

    result = renderer.post_process(input_nodes)

    assert result[0].get("custom_marker") is True
