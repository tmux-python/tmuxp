"""Tests for workspace builder resolution (:mod:`tmuxp.workspace.builder.registry`)."""

from __future__ import annotations

import sys
import textwrap
import typing as t

import pytest

from tmuxp import exc
from tmuxp.workspace import loader
from tmuxp.workspace.builder import registry
from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder

if t.TYPE_CHECKING:
    import pathlib

    from libtmux.server import Server

VALID = "tests.fixtures.workspace_builders.valid"
INVALID = "tests.fixtures.workspace_builders.invalid"


def test_resolve_default_returns_classic() -> None:
    """An absent workspace_builder resolves to the classic builder."""
    assert registry.resolve_builder_class({}) is ClassicWorkspaceBuilder


def test_resolve_entry_point_classic() -> None:
    """The 'classic' entry point resolves to the classic builder."""
    resolved = registry.resolve_builder_class({"workspace_builder": "classic"})
    assert resolved is ClassicWorkspaceBuilder


def test_resolve_dotted_object_reference() -> None:
    """A ``module:attr`` reference resolves and validates."""
    from tests.fixtures.workspace_builders.valid import CustomBuilder

    resolved = registry.resolve_builder_class(
        {"workspace_builder": f"{VALID}:CustomBuilder"},
    )
    assert resolved is CustomBuilder


def test_resolve_dotted_path_reference() -> None:
    """A dotted ``module.attr`` path resolves and validates."""
    from tests.fixtures.workspace_builders.valid import CustomBuilder

    resolved = registry.resolve_builder_class(
        {"workspace_builder": f"{VALID}.CustomBuilder"},
    )
    assert resolved is CustomBuilder


def test_resolve_compat_alias_path() -> None:
    """The historical ``tmuxp.workspace.builder:WorkspaceBuilder`` still resolves."""
    resolved = registry.resolve_builder_class(
        {"workspace_builder": "tmuxp.workspace.builder:WorkspaceBuilder"},
    )
    assert resolved is ClassicWorkspaceBuilder


def test_resolve_not_found_bare_name() -> None:
    """An unknown bare name raises WorkspaceBuilderNotFound."""
    with pytest.raises(exc.WorkspaceBuilderNotFound):
        registry.resolve_builder_class({"workspace_builder": "nonexistent-builder"})


def test_resolve_import_error() -> None:
    """An unimportable dotted path raises WorkspaceBuilderImportError."""
    with pytest.raises(exc.WorkspaceBuilderImportError):
        registry.resolve_builder_class(
            {"workspace_builder": "tmuxp.does_not_exist:Thing"},
        )


def test_resolve_invalid_builder() -> None:
    """A class without a build method raises InvalidWorkspaceBuilder."""
    with pytest.raises(exc.InvalidWorkspaceBuilder):
        registry.resolve_builder_class(
            {"workspace_builder": f"{INVALID}:NotABuilder"},
        )


def test_available_builders_includes_classic() -> None:
    """The classic entry point is discoverable."""
    assert "classic" in registry.available_builders()


def test_resolve_builder_paths_absent() -> None:
    """No workspace_builder_paths resolves to an empty list."""
    assert registry.resolve_builder_paths({}, None) == []


def test_resolve_builder_paths_requires_directory(tmp_path: pathlib.Path) -> None:
    """A missing directory raises WorkspaceBuilderPathError."""
    with pytest.raises(exc.WorkspaceBuilderPathError):
        registry.resolve_builder_paths(
            {"workspace_builder_paths": [str(tmp_path / "missing")]},
            None,
        )


def test_resolve_builder_paths_relative_to_workspace_file(
    tmp_path: pathlib.Path,
) -> None:
    """Relative entries resolve against the workspace file's directory."""
    builders_dir = tmp_path / "builders"
    builders_dir.mkdir()
    workspace_file = tmp_path / "workspace.yaml"
    workspace_file.write_text("session_name: x\n", encoding="utf-8")

    resolved = registry.resolve_builder_paths(
        {"workspace_builder_paths": ["builders"]},
        workspace_file,
    )
    assert resolved == [builders_dir.resolve()]


def test_prepended_sys_path_restores(tmp_path: pathlib.Path) -> None:
    """The sandbox restores sys.path exactly on exit."""
    before = list(sys.path)
    with registry.prepended_sys_path([tmp_path]):
        assert sys.path[0] == str(tmp_path)
    assert sys.path == before


def test_trusted_path_enables_import(tmp_path: pathlib.Path) -> None:
    """A builder in a trusted path imports only while the path is active."""
    sys.modules.pop("ext_builder_trusted", None)
    module = tmp_path / "ext_builder_trusted.py"
    module.write_text(
        textwrap.dedent(
            '''\
"""External builder for trusted-path tests."""

from __future__ import annotations

from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder


class ExternalBuilder(ClassicWorkspaceBuilder):
    """External custom builder."""
''',
        ),
        encoding="utf-8",
    )
    config = {"workspace_builder": "ext_builder_trusted:ExternalBuilder"}

    with pytest.raises(exc.WorkspaceBuilderImportError):
        registry.resolve_builder_class(config)

    paths = registry.resolve_builder_paths(
        {"workspace_builder_paths": [str(tmp_path)]},
        None,
    )
    with registry.prepended_sys_path(paths):
        resolved = registry.resolve_builder_class(config)
    assert resolved.__name__ == "ExternalBuilder"


def test_resolve_and_build_selected_builder(server: Server) -> None:
    """A config selecting a builder builds through the resolved class."""
    config = loader.expand(
        {
            "session_name": "registry-build",
            "workspace_builder": "classic",
            "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
        },
    )
    builder_cls = registry.resolve_builder_class(config)
    builder = builder_cls(session_config=config, server=server)
    builder.build()
    assert builder.session.name == "registry-build"
    builder.session.kill()
