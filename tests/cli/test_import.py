"""CLI tests for tmuxp import."""

from __future__ import annotations

import contextlib
import io
import typing as t

import pytest

from tests.fixtures import utils as test_utils
from tmuxp import cli

if t.TYPE_CHECKING:
    import pathlib


class ImportTestFixture(t.NamedTuple):
    """Test fixture for basic tmuxp import command tests."""

    test_id: str
    cli_args: list[str]


IMPORT_TEST_FIXTURES: list[ImportTestFixture] = [
    ImportTestFixture(
        test_id="basic_import",
        cli_args=["import"],
    ),
]


@pytest.mark.parametrize(
    list(ImportTestFixture._fields),
    IMPORT_TEST_FIXTURES,
    ids=[test.test_id for test in IMPORT_TEST_FIXTURES],
)
def test_import(
    test_id: str,
    cli_args: list[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Basic CLI test for tmuxp import."""
    cli.cli(cli_args)
    result = capsys.readouterr()
    assert "tmuxinator" in result.out
    assert "teamocil" in result.out


class ImportTeamocilTestFixture(t.NamedTuple):
    """Test fixture for tmuxp import teamocil command tests."""

    test_id: str
    cli_args: list[str]
    inputs: list[str]


IMPORT_TEAMOCIL_TEST_FIXTURES: list[ImportTeamocilTestFixture] = [
    ImportTeamocilTestFixture(
        test_id="import_teamocil_config_file",
        cli_args=["import", "teamocil", "./.teamocil/config.yaml"],
        inputs=["\n", "y\n", "./la.yaml\n", "y\n"],
    ),
    ImportTeamocilTestFixture(
        test_id="import_teamocil_config_file_exists",
        cli_args=["import", "teamocil", "./.teamocil/config.yaml"],
        inputs=["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
    ),
    ImportTeamocilTestFixture(
        test_id="import_teamocil_config_name",
        cli_args=["import", "teamocil", "config"],
        inputs=["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
    ),
]


@pytest.mark.parametrize(
    list(ImportTeamocilTestFixture._fields),
    IMPORT_TEAMOCIL_TEST_FIXTURES,
    ids=[test.test_id for test in IMPORT_TEAMOCIL_TEST_FIXTURES],
)
def test_import_teamocil(
    test_id: str,
    cli_args: list[str],
    inputs: list[str],
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


class ImportTmuxinatorTestFixture(t.NamedTuple):
    """Test fixture for tmuxp import tmuxinator command tests."""

    test_id: str
    cli_args: list[str]
    inputs: list[str]


IMPORT_TMUXINATOR_TEST_FIXTURES: list[ImportTmuxinatorTestFixture] = [
    ImportTmuxinatorTestFixture(
        test_id="import_tmuxinator_config_file",
        cli_args=["import", "tmuxinator", "./.tmuxinator/config.yaml"],
        inputs=["\n", "y\n", "./la.yaml\n", "y\n"],
    ),
    ImportTmuxinatorTestFixture(
        test_id="import_tmuxinator_config_file_exists",
        cli_args=["import", "tmuxinator", "./.tmuxinator/config.yaml"],
        inputs=["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
    ),
    ImportTmuxinatorTestFixture(
        test_id="import_tmuxinator_config_name",
        cli_args=["import", "tmuxinator", "config"],
        inputs=["\n", "y\n", "./exists.yaml\n", "./la.yaml\n", "y\n"],
    ),
]


@pytest.mark.parametrize(
    list(ImportTmuxinatorTestFixture._fields),
    IMPORT_TMUXINATOR_TEST_FIXTURES,
    ids=[test.test_id for test in IMPORT_TMUXINATOR_TEST_FIXTURES],
)
def test_import_tmuxinator(
    test_id: str,
    cli_args: list[str],
    inputs: list[str],
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
