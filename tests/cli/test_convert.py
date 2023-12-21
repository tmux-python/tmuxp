"""CLI tests for tmuxp convert."""
import contextlib
import io
import json
import pathlib
import typing as t

import pytest

from tmuxp import cli


@pytest.mark.parametrize(
    "cli_args",
    [
        (["convert", "."]),
        (["convert", ".tmuxp.yaml"]),
        (["convert", ".tmuxp.yaml", "-y"]),
        (["convert", ".tmuxp.yml"]),
        (["convert", ".tmuxp.yml", "-y"]),
    ],
)
def test_convert(
    cli_args: t.List[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parametrized tests for tmuxp convert."""
    # create dummy tmuxp yaml so we don't get yelled at
    filename = cli_args[1]
    if filename == ".":
        filename = ".tmuxp.yaml"
    file_ext = filename.rsplit(".", 1)[-1]
    assert file_ext in ["yaml", "yml"], file_ext
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


@pytest.mark.parametrize(
    "cli_args",
    [
        (["convert", "."]),
        (["convert", ".tmuxp.json"]),
        (["convert", ".tmuxp.json", "-y"]),
    ],
)
def test_convert_json(
    cli_args: t.List[str],
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
