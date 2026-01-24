"""Compatibility utilities for module loading.

This module provides utilities for loading Python modules safely,
including mock handling for imports that may fail during documentation
builds.

Unlike sphinx-argparse, this module does NOT depend on autodoc's mock
functionality, which moved in Sphinx 9.x.
"""

from __future__ import annotations

import contextlib
import importlib
import sys
import typing as t

if t.TYPE_CHECKING:
    import argparse
    from collections.abc import Iterator


class MockModule:
    """Simple mock for unavailable imports.

    This class provides a minimal mock that can be used as a placeholder
    for modules that aren't available during documentation builds.

    Parameters
    ----------
    name : str
        The module name being mocked.

    Examples
    --------
    >>> mock = MockModule("mypackage.submodule")
    >>> mock.__name__
    'mypackage.submodule'
    >>> child = mock.child_attr
    >>> child.__name__
    'mypackage.submodule.child_attr'
    >>> callable(mock.some_function)
    True
    >>> mock.some_function()
    <MockModule: mypackage.submodule.some_function>
    """

    def __init__(self, name: str) -> None:
        """Initialize the mock module."""
        self.__name__ = name
        self._name = name

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<MockModule: {self._name}>"

    def __getattr__(self, name: str) -> MockModule:
        """Return a child mock for any attribute access.

        Parameters
        ----------
        name : str
            The attribute name.

        Returns
        -------
        MockModule
            A new mock for the child attribute.
        """
        return MockModule(f"{self._name}.{name}")

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> MockModule:
        """Return self when called as a function.

        Parameters
        ----------
        *args : t.Any
            Positional arguments (ignored).
        **kwargs : t.Any
            Keyword arguments (ignored).

        Returns
        -------
        MockModule
            Self.
        """
        return self


@contextlib.contextmanager
def mock_imports(modules: list[str]) -> Iterator[None]:
    """Context manager to mock missing imports.

    This provides a simple way to temporarily add mock modules to
    sys.modules, allowing imports to succeed during documentation builds
    even when the actual modules aren't available.

    Parameters
    ----------
    modules : list[str]
        List of module names to mock.

    Yields
    ------
    None
        Context manager yields nothing.

    Examples
    --------
    >>> import sys
    >>> "fake_module" in sys.modules
    False
    >>> with mock_imports(["fake_module", "fake_module.sub"]):
    ...     import fake_module
    ...     fake_module.__name__
    'fake_module'
    >>> "fake_module" in sys.modules
    False
    """
    mocked: dict[str, MockModule] = {}

    for name in modules:
        if name not in sys.modules:
            mocked[name] = MockModule(name)
            sys.modules[name] = mocked[name]  # type: ignore[assignment]

    try:
        yield
    finally:
        for name in mocked:
            del sys.modules[name]


def import_module(module_name: str) -> t.Any:
    """Import a module by name.

    Parameters
    ----------
    module_name : str
        The fully qualified module name.

    Returns
    -------
    t.Any
        The imported module.

    Raises
    ------
    ImportError
        If the module cannot be imported.

    Examples
    --------
    >>> mod = import_module("argparse")
    >>> hasattr(mod, "ArgumentParser")
    True
    """
    return importlib.import_module(module_name)


def get_parser_from_module(
    module_name: str,
    func_name: str,
    mock_modules: list[str] | None = None,
) -> argparse.ArgumentParser:
    """Import a module and call a function to get an ArgumentParser.

    Parameters
    ----------
    module_name : str
        The module containing the parser factory function.
    func_name : str
        The name of the function that returns an ArgumentParser.
        Can be a dotted path like "Class.method".
    mock_modules : list[str] | None
        Optional list of module names to mock during import.

    Returns
    -------
    argparse.ArgumentParser
        The argument parser returned by the function.

    Raises
    ------
    ImportError
        If the module cannot be imported.
    AttributeError
        If the function is not found.
    TypeError
        If the function doesn't return an ArgumentParser.

    Examples
    --------
    Load tmuxp's parser factory:

    >>> parser = get_parser_from_module("tmuxp.cli", "create_parser")
    >>> parser.prog
    'tmuxp'
    >>> hasattr(parser, 'parse_args')
    True
    """
    ctx = mock_imports(mock_modules) if mock_modules else contextlib.nullcontext()

    with ctx:
        module = import_module(module_name)

        # Handle dotted paths like "Class.method"
        obj = module
        for part in func_name.split("."):
            obj = getattr(obj, part)

        # Call the function if it's callable
        parser = obj() if callable(obj) else obj

        # Validate the return type at runtime
        import argparse as argparse_module

        if not isinstance(parser, argparse_module.ArgumentParser):
            msg = (
                f"{module_name}:{func_name} returned {type(parser).__name__}, "
                f"expected ArgumentParser"
            )
            raise TypeError(msg)

        return parser


def get_parser_from_entry_point(
    entry_point: str,
    mock_modules: list[str] | None = None,
) -> argparse.ArgumentParser:
    """Get an ArgumentParser from a setuptools-style entry point string.

    Parameters
    ----------
    entry_point : str
        Entry point in the format "module:function" or "module:Class.method".
    mock_modules : list[str] | None
        Optional list of module names to mock during import.

    Returns
    -------
    argparse.ArgumentParser
        The argument parser.

    Raises
    ------
    ValueError
        If the entry point format is invalid.

    Examples
    --------
    Load tmuxp's parser using entry point syntax:

    >>> parser = get_parser_from_entry_point("tmuxp.cli:create_parser")
    >>> parser.prog
    'tmuxp'

    Invalid format raises ValueError:

    >>> get_parser_from_entry_point("no_colon")
    Traceback (most recent call last):
        ...
    ValueError: Invalid entry point format: 'no_colon'. Expected 'module:function'
    """
    if ":" not in entry_point:
        msg = f"Invalid entry point format: {entry_point!r}. Expected 'module:function'"
        raise ValueError(msg)

    module_name, func_name = entry_point.split(":", 1)
    return get_parser_from_module(module_name, func_name, mock_modules)
