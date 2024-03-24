"""CLI tests for tmuxp import."""

import contextlib
import io
import pathlib
import typing as t

import pytest

from tests.fixtures import utils as test_utils
from tmuxp import cli


@pytest.mark.parametrize("cli_args", [(["import"])])
def test_import(
    cli_args: t.List[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Basic CLI test for tmuxp import."""
    cli.cli(cli_args)
    result = capsys.readouterr()
    assert "tmuxinator" in result.out
    assert "teamocil" in result.out


@pytest.mark.parametrize(
    ("cli_args", "inputs"),
    [
        (
            ["import", "teamocil", "./.teamocil/config.yaml"],
            ["\n", "y\n", "./la.yaml\n", "y\n"],
        ),
        (
            ["import", "teamocil", "./.teamocil/config.yaml"],
            ["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
        ),
        (
            ["import", "teamocil", "config"],
            ["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
        ),
    ],
)
def test_import_teamocil(
    cli_args: t.List[str],
    inputs: t.List[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI test for tmuxp import w/ teamocil."""
    teamocil_config = test_utils.read_workspace_file("import_teamocil/test4.yaml")

    teamocil_path = tmp_path / ".teamocil"
    teamocil_path.mkdir()

    teamocil_config_path = teamocil_path / "config.yaml"
    teamocil_config_path.write_text(teamocil_config, encoding="utf-8")

    exists_yaml = tmp_path / "exists.yaml"
    exists_yaml.touch()

    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("".join(inputs)))

    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    new_config_yaml = tmp_path / "la.yaml"
    assert new_config_yaml.exists()


@pytest.mark.parametrize(
    ("cli_args", "inputs"),
    [
        (
            ["import", "tmuxinator", "./.tmuxinator/config.yaml"],
            ["\n", "y\n", "./la.yaml\n", "y\n"],
        ),
        (
            ["import", "tmuxinator", "./.tmuxinator/config.yaml"],
            ["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
        ),
        (
            ["import", "tmuxinator", "config"],
            ["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
        ),
    ],
)
def test_import_tmuxinator(
    cli_args: t.List[str],
    inputs: t.List[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI test for tmuxp import w/ tmuxinator."""
    tmuxinator_config = test_utils.read_workspace_file("import_tmuxinator/test3.yaml")

    tmuxinator_path = tmp_path / ".tmuxinator"
    tmuxinator_path.mkdir()

    tmuxinator_config_path = tmuxinator_path / "config.yaml"
    tmuxinator_config_path.write_text(tmuxinator_config, encoding="utf-8")

    exists_yaml = tmp_path / "exists.yaml"
    exists_yaml.touch()

    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr("sys.stdin", io.StringIO("".join(inputs)))
    with contextlib.suppress(SystemExit):
        cli.cli(cli_args)

    new_config_yaml = tmp_path / "la.yaml"
    assert new_config_yaml.exists()
