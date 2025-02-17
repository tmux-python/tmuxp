"""CLI tests for tmuxp convert."""

from __future__ import annotations

import contextlib
import io
import json
import typing as t

import pytest

from tmuxp import cli

if t.TYPE_CHECKING:
    import pathlib


class ConvertTestFixture(t.NamedTuple):
    """Test fixture for tmuxp convert command tests."""

    test_id: str
    cli_args: list[str]


CONVERT_TEST_FIXTURES: list[ConvertTestFixture] = [
    ConvertTestFixture(
        test_id="convert_current_dir",
        cli_args=["convert", "."],
    ),
    ConvertTestFixture(
        test_id="convert_yaml_file",
        cli_args=["convert", ".tmuxp.yaml"],
    ),
    ConvertTestFixture(
        test_id="convert_yaml_file_auto_confirm",
        cli_args=["convert", ".tmuxp.yaml", "-y"],
    ),
    ConvertTestFixture(
        test_id="convert_yml_file",
        cli_args=["convert", ".tmuxp.yml"],
    ),
    ConvertTestFixture(
        test_id="convert_yml_file_auto_confirm",
        cli_args=["convert", ".tmuxp.yml", "-y"],
    ),
]


@pytest.mark.parametrize(
    list(ConvertTestFixture._fields),
    CONVERT_TEST_FIXTURES,
    ids=[test.test_id for test in CONVERT_TEST_FIXTURES],
)
def test_convert(
    test_id: str,
    cli_args: list[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parametrized tests for tmuxp convert."""
    # create dummy tmuxp yaml so we don't get yelled at
    filename = cli_args[1]
    if filename == ".":
        filename = ".tmuxp.yaml"
    file_ext = filename.rsplit(".", 1)[-1]
    assert file_ext in {"yaml", "yml"}, file_ext
    workspace_file_path = tmp_path / filename
    workspace_file_path.write_text("\nsession_name: hello\n", encoding="utf-8")
    oh_my_zsh_path = tmp_path / ".oh-my-zsh"
    oh_my_zsh_path.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)

    # If autoconfirm (-y) no need to prompt y
    input_args = "y\ny\n" if "-y" not in cli_args else ""

    monkeypatch.setattr("sys.stdin", io.StringIO(input_args))
    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    tmuxp_json = tmp_path / ".tmuxp.json"
    assert tmuxp_json.exists()
    assert tmuxp_json.open().read() == json.dumps({"session_name": "hello"}, indent=2)


class ConvertJsonTestFixture(t.NamedTuple):
    """Test fixture for tmuxp convert json command tests."""

    test_id: str
    cli_args: list[str]


CONVERT_JSON_TEST_FIXTURES: list[ConvertJsonTestFixture] = [
    ConvertJsonTestFixture(
        test_id="convert_json_current_dir",
        cli_args=["convert", "."],
    ),
    ConvertJsonTestFixture(
        test_id="convert_json_file",
        cli_args=["convert", ".tmuxp.json"],
    ),
    ConvertJsonTestFixture(
        test_id="convert_json_file_auto_confirm",
        cli_args=["convert", ".tmuxp.json", "-y"],
    ),
]


@pytest.mark.parametrize(
    list(ConvertJsonTestFixture._fields),
    CONVERT_JSON_TEST_FIXTURES,
    ids=[test.test_id for test in CONVERT_JSON_TEST_FIXTURES],
)
def test_convert_json(
    test_id: str,
    cli_args: list[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI test using tmuxp convert to convert configuration from json to yaml."""
    # create dummy tmuxp yaml so we don't get yelled at
    json_config = tmp_path / ".tmuxp.json"
    json_config.write_text('{"session_name": "hello"}', encoding="utf-8")
    oh_my_zsh_path = tmp_path / ".oh-my-zsh"
    oh_my_zsh_path.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)

    # If autoconfirm (-y) no need to prompt y
    input_args = "y\ny\n" if "-y" not in cli_args else ""

    monkeypatch.setattr("sys.stdin", io.StringIO(input_args))
    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    tmuxp_yaml = tmp_path / ".tmuxp.yaml"
    assert tmuxp_yaml.exists()
    assert tmuxp_yaml.open().read() == "session_name: hello\n"
