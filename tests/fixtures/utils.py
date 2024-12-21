"""Utility functions for tmuxp fixtures."""

import pathlib
import typing as t

from tests.constants import FIXTURE_PATH


def get_workspace_file(
    file: t.Union[str, pathlib.Path],
) -> pathlib.Path:
    """Return fixture data, relative to __file__."""
    if isinstance(file, str):
        file = pathlib.Path(file)

    return FIXTURE_PATH / file


def read_workspace_file(
    file: t.Union[pathlib.Path, str],
) -> str:
    """Return fixture data, relative to __file__."""
    if isinstance(file, str):
        file = pathlib.Path(file)

    return get_workspace_file(file).open().read()


def write_config(
    config_path: pathlib.Path,
    filename: str,
    content: str,
) -> pathlib.Path:
    """Write configuration content to file."""
    config = config_path / filename
    config.write_text(content, encoding="utf-8")
    return config
