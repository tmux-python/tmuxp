"""Tests for sphinx_argparse_neo.compat module."""

from __future__ import annotations

import sys
import typing as t

import pytest
from sphinx_argparse_neo.compat import (
    MockModule,
    get_parser_from_entry_point,
    get_parser_from_module,
    import_module,
    mock_imports,
)

# --- MockModule tests ---


def test_mock_module_name() -> None:
    """Test MockModule name attribute."""
    mock = MockModule("mypackage.submodule")
    assert mock.__name__ == "mypackage.submodule"


def test_mock_module_repr() -> None:
    """Test MockModule string representation."""
    mock = MockModule("mypackage")
    assert repr(mock) == "<MockModule: mypackage>"


def test_mock_module_getattr() -> None:
    """Test MockModule attribute access."""
    mock = MockModule("mypackage")
    child = mock.submodule

    assert isinstance(child, MockModule)
    assert child.__name__ == "mypackage.submodule"


def test_mock_module_nested_getattr() -> None:
    """Test MockModule nested attribute access."""
    mock = MockModule("pkg")
    deep = mock.level1.level2.level3

    assert deep.__name__ == "pkg.level1.level2.level3"


def test_mock_module_callable() -> None:
    """Test MockModule is callable."""
    mock = MockModule("mypackage")
    result = mock()

    assert result is mock


def test_mock_module_callable_with_args() -> None:
    """Test MockModule callable with arguments."""
    mock = MockModule("mypackage")
    result = mock(1, 2, 3, key="value")

    assert result is mock


def test_mock_module_chained_call() -> None:
    """Test MockModule chained attribute access and call."""
    mock = MockModule("pkg")
    result = mock.SomeClass()

    assert isinstance(result, MockModule)


# --- mock_imports context manager tests ---


def test_mock_imports_adds_to_sys_modules() -> None:
    """Test that mock_imports adds modules to sys.modules."""
    module_name = "test_fake_module_xyz"

    assert module_name not in sys.modules

    with mock_imports([module_name]):
        assert module_name in sys.modules
        assert isinstance(sys.modules[module_name], MockModule)

    assert module_name not in sys.modules


def test_mock_imports_multiple_modules() -> None:
    """Test mocking multiple modules."""
    modules = ["fake_a", "fake_b", "fake_c"]

    with mock_imports(modules):
        for name in modules:
            assert name in sys.modules

    for name in modules:
        assert name not in sys.modules


def test_mock_imports_nested_modules() -> None:
    """Test mocking nested module paths."""
    modules = ["fake_pkg", "fake_pkg.sub", "fake_pkg.sub.deep"]

    with mock_imports(modules):
        for name in modules:
            assert name in sys.modules

    for name in modules:
        assert name not in sys.modules


def test_mock_imports_does_not_override_existing() -> None:
    """Test that mock_imports doesn't override existing modules."""
    # argparse is already imported
    original = sys.modules["argparse"]

    with mock_imports(["argparse"]):
        # Should not be replaced
        assert sys.modules["argparse"] is original

    assert sys.modules["argparse"] is original


def test_mock_imports_cleanup_on_exception() -> None:
    """Test that mock_imports cleans up even on exception."""
    module_name = "fake_exception_test"
    exc_msg = "Test exception"

    with pytest.raises(ValueError), mock_imports([module_name]):
        assert module_name in sys.modules
        raise ValueError(exc_msg)

    assert module_name not in sys.modules


def test_mock_imports_allows_import() -> None:
    """Test that mocked modules can be imported."""
    module_name = "fake_importable"

    with mock_imports([module_name]):
        # This should work without ImportError
        import fake_importable  # type: ignore[import-not-found]

        assert fake_importable.__name__ == "fake_importable"


# --- import_module tests ---


def test_import_module_builtin() -> None:
    """Test importing a built-in module."""
    mod = import_module("argparse")
    assert hasattr(mod, "ArgumentParser")


def test_import_module_stdlib() -> None:
    """Test importing a stdlib module."""
    mod = import_module("os.path")
    assert hasattr(mod, "join")


def test_import_module_not_found() -> None:
    """Test importing a non-existent module."""
    with pytest.raises(ModuleNotFoundError):
        import_module("nonexistent_module_xyz")


# --- get_parser_from_module tests ---


def test_get_parser_from_module_argparse() -> None:
    """Test getting parser from argparse module itself."""
    # Create a test module with a parser factory
    import types

    test_module = types.ModuleType("test_parser_module")

    def create_parser() -> t.Any:
        import argparse

        return argparse.ArgumentParser(prog="test")

    test_module.create_parser = create_parser  # type: ignore[attr-defined]
    sys.modules["test_parser_module"] = test_module

    try:
        parser = get_parser_from_module("test_parser_module", "create_parser")
        assert parser.prog == "test"
    finally:
        del sys.modules["test_parser_module"]


def test_get_parser_from_module_with_mock() -> None:
    """Test getting parser with mocked dependencies."""
    import types

    test_module = types.ModuleType("test_mock_parser")

    def create_parser() -> t.Any:
        import argparse

        return argparse.ArgumentParser(prog="mocked")

    test_module.create_parser = create_parser  # type: ignore[attr-defined]
    sys.modules["test_mock_parser"] = test_module

    try:
        parser = get_parser_from_module(
            "test_mock_parser",
            "create_parser",
            mock_modules=["fake_dependency"],
        )
        assert parser.prog == "mocked"
    finally:
        del sys.modules["test_mock_parser"]


def test_get_parser_from_module_dotted_path() -> None:
    """Test getting parser from class method."""
    import types

    test_module = types.ModuleType("test_class_parser")

    class CLI:
        @staticmethod
        def create_parser() -> t.Any:
            import argparse

            return argparse.ArgumentParser(prog="from_class")

    test_module.CLI = CLI  # type: ignore[attr-defined]
    sys.modules["test_class_parser"] = test_module

    try:
        parser = get_parser_from_module("test_class_parser", "CLI.create_parser")
        assert parser.prog == "from_class"
    finally:
        del sys.modules["test_class_parser"]


def test_get_parser_from_module_not_found() -> None:
    """Test error when module not found."""
    with pytest.raises(ModuleNotFoundError):
        get_parser_from_module("nonexistent_xyz", "func")


def test_get_parser_from_module_func_not_found() -> None:
    """Test error when function not found."""
    with pytest.raises(AttributeError):
        get_parser_from_module("argparse", "nonexistent_func")


# --- get_parser_from_entry_point tests ---


def test_get_parser_from_entry_point_valid() -> None:
    """Test parsing valid entry point format."""
    import types

    test_module = types.ModuleType("test_entry_point")

    def get_parser() -> t.Any:
        import argparse

        return argparse.ArgumentParser(prog="entry")

    test_module.get_parser = get_parser  # type: ignore[attr-defined]
    sys.modules["test_entry_point"] = test_module

    try:
        parser = get_parser_from_entry_point("test_entry_point:get_parser")
        assert parser.prog == "entry"
    finally:
        del sys.modules["test_entry_point"]


def test_get_parser_from_entry_point_invalid_format() -> None:
    """Test error on invalid entry point format."""
    with pytest.raises(ValueError) as exc_info:
        get_parser_from_entry_point("no_colon_separator")

    assert "Invalid entry point format" in str(exc_info.value)


def test_get_parser_from_entry_point_with_class() -> None:
    """Test entry point with class method."""
    import types

    test_module = types.ModuleType("test_entry_class")

    class Factory:
        @staticmethod
        def parser() -> t.Any:
            import argparse

            return argparse.ArgumentParser(prog="factory")

    test_module.Factory = Factory  # type: ignore[attr-defined]
    sys.modules["test_entry_class"] = test_module

    try:
        parser = get_parser_from_entry_point("test_entry_class:Factory.parser")
        assert parser.prog == "factory"
    finally:
        del sys.modules["test_entry_class"]


def test_get_parser_from_entry_point_with_mock() -> None:
    """Test entry point with mocked modules."""
    import types

    test_module = types.ModuleType("test_entry_mock")

    def make_parser() -> t.Any:
        import argparse

        return argparse.ArgumentParser(prog="with_mock")

    test_module.make_parser = make_parser  # type: ignore[attr-defined]
    sys.modules["test_entry_mock"] = test_module

    try:
        parser = get_parser_from_entry_point(
            "test_entry_mock:make_parser",
            mock_modules=["some_optional_dep"],
        )
        assert parser.prog == "with_mock"
    finally:
        del sys.modules["test_entry_mock"]
