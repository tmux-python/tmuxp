"""CLI tests for tmuxp import."""

from __future__ import annotations

import contextlib
import io
import typing as t

import pytest

from tests.fixtures import utils as test_utils
from tmuxp import cli
from tmuxp.cli import import_config as import_config_module

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


def test_get_tmuxinator_base_indices_reads_live_tmux_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tmuxinator import reads tmux base indices from live tmux options."""

    class FakeTmuxResponse(t.NamedTuple):
        """Fake tmux command response."""

        returncode: int
        stdout: list[str]

    def fake_tmux_cmd(*args: str) -> FakeTmuxResponse:
        if args == ("show-options", "-gv", "base-index"):
            return FakeTmuxResponse(returncode=0, stdout=["1"])
        if args == ("show-window-options", "-gv", "pane-base-index"):
            return FakeTmuxResponse(returncode=0, stdout=["2"])
        msg = f"unexpected tmux args: {args!r}"
        raise AssertionError(msg)

    monkeypatch.setattr(import_config_module, "tmux_cmd", fake_tmux_cmd)

    assert import_config_module._get_tmuxinator_base_indices() == (1, 2)


def test_get_tmuxinator_base_indices_falls_back_when_tmux_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tmuxinator import falls back to tmux defaults when lookup fails."""

    def raise_tmux_error(*args: str) -> t.NoReturn:
        msg = f"tmux unavailable for {args!r}"
        raise RuntimeError(msg)

    monkeypatch.setattr(import_config_module, "tmux_cmd", raise_tmux_error)

    assert import_config_module._get_tmuxinator_base_indices() == (0, 0)


def test_command_import_tmuxinator_passes_resolved_base_indices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tmuxinator import command passes resolved tmux indices to the importer."""
    captured: dict[str, t.Any] = {}

    def fake_find_workspace_file(
        workspace_file: str,
        workspace_dir: t.Any,
    ) -> str:
        captured["workspace_file"] = workspace_file
        captured["workspace_dir"] = workspace_dir
        return workspace_file

    def fake_import_config(
        workspace_file: str,
        importfunc: t.Callable[[dict[str, t.Any]], dict[str, t.Any]],
        parser: t.Any = None,
        colors: t.Any = None,
    ) -> None:
        captured["workspace_file"] = workspace_file
        captured["parser"] = parser
        captured["colors"] = colors
        captured["imported"] = importfunc(
            {
                "name": "sample",
                "startup_window": 1,
                "startup_pane": 2,
                "windows": [{"editor": ["vim", "logs"]}],
            }
        )

    monkeypatch.setattr(
        import_config_module,
        "find_workspace_file",
        fake_find_workspace_file,
    )
    monkeypatch.setattr(import_config_module, "import_config", fake_import_config)
    monkeypatch.setattr(
        import_config_module,
        "_get_tmuxinator_base_indices",
        lambda: (1, 2),
    )

    import_config_module.command_import_tmuxinator("sample.yml")

    imported = captured["imported"]
    assert imported["windows"][0]["focus"] is True
    assert imported["windows"][0]["panes"][0] == {
        "shell_command": ["vim"],
        "focus": True,
    }
