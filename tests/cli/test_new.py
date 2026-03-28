"""Test tmuxp new command."""

from __future__ import annotations

import pathlib
import typing as t

import pytest

from tmuxp import cli
from tmuxp.cli.new import WORKSPACE_TEMPLATE


class NewTestFixture(t.NamedTuple):
    """Test fixture for tmuxp new command tests."""

    test_id: str
    cli_args: list[str]
    workspace_name: str
    expect_created: bool
    pre_existing: bool


NEW_TEST_FIXTURES: list[NewTestFixture] = [
    NewTestFixture(
        test_id="new-workspace",
        cli_args=["new", "myproject"],
        workspace_name="myproject",
        expect_created=True,
        pre_existing=False,
    ),
    NewTestFixture(
        test_id="new-existing-workspace",
        cli_args=["new", "existing"],
        workspace_name="existing",
        expect_created=False,
        pre_existing=True,
    ),
]


@pytest.mark.parametrize(
    list(NewTestFixture._fields),
    NEW_TEST_FIXTURES,
    ids=[test.test_id for test in NEW_TEST_FIXTURES],
)
def test_new(
    tmp_path: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    test_id: str,
    cli_args: list[str],
    workspace_name: str,
    expect_created: bool,
    pre_existing: bool,
) -> None:
    """Test creating a new workspace config."""
    config_dir = tmp_path / "tmuxp"
    config_dir.mkdir()
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(config_dir))
    monkeypatch.setenv("EDITOR", "true")

    workspace_path = config_dir / f"{workspace_name}.yaml"

    if pre_existing:
        original_content = "session_name: original\n"
        workspace_path.write_text(original_content)

    cli.cli(cli_args)

    captured = capsys.readouterr()
    assert workspace_path.exists()

    if expect_created:
        expected_content = WORKSPACE_TEMPLATE.format(name=workspace_name)
        assert workspace_path.read_text() == expected_content
        assert "Created" in captured.out
    else:
        assert workspace_path.read_text() == original_content
        assert "already exists" in captured.out


def test_new_creates_workspace_dir(
    tmp_path: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that 'new' creates the workspace directory if it doesn't exist."""
    config_dir = tmp_path / "nonexistent"
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(config_dir))
    monkeypatch.setenv("EDITOR", "true")

    assert not config_dir.exists()

    cli.cli(["new", "myproject"])

    assert config_dir.exists()
    workspace_path = config_dir / "myproject.yaml"
    assert workspace_path.exists()


class EditorFixture(t.NamedTuple):
    """Fixture for EDITOR environment variable handling."""

    test_id: str
    editor: str
    expect_error_output: bool


EDITOR_FIXTURES: list[EditorFixture] = [
    EditorFixture(
        test_id="valid_editor",
        editor="true",
        expect_error_output=False,
    ),
    EditorFixture(
        test_id="editor_with_flags",
        editor="true --ignored-flag",
        expect_error_output=False,
    ),
]


@pytest.mark.parametrize(
    list(EditorFixture._fields),
    EDITOR_FIXTURES,
    ids=[f.test_id for f in EDITOR_FIXTURES],
)
def test_new_editor_handling(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    test_id: str,
    editor: str,
    expect_error_output: bool,
) -> None:
    """Test EDITOR handling: flags and valid editor."""
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(tmp_path))
    monkeypatch.setenv("EDITOR", editor)

    cli.cli(["new", f"editortest_{test_id}"])

    workspace_path = tmp_path / f"editortest_{test_id}.yaml"
    assert workspace_path.exists()

    captured = capsys.readouterr()
    if expect_error_output:
        assert "Editor not found" in captured.out
    else:
        assert "Editor not found" not in captured.out


class NewExitCodeFixture(t.NamedTuple):
    """Test fixture for tmuxp new error exit codes."""

    test_id: str
    cli_args: list[str]
    editor: str
    expected_exit_code: int
    expected_output_fragment: str


NEW_EXIT_CODE_FIXTURES: list[NewExitCodeFixture] = [
    NewExitCodeFixture(
        test_id="no_args",
        cli_args=["new"],
        editor="true",
        expected_exit_code=1,
        expected_output_fragment="",
    ),
    NewExitCodeFixture(
        test_id="missing_editor",
        cli_args=["new", "editortest_missing"],
        editor="nonexistent_editor_binary_xyz",
        expected_exit_code=1,
        expected_output_fragment="Editor not found",
    ),
]


@pytest.mark.parametrize(
    list(NewExitCodeFixture._fields),
    NEW_EXIT_CODE_FIXTURES,
    ids=[f.test_id for f in NEW_EXIT_CODE_FIXTURES],
)
def test_new_error_exits_nonzero(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    test_id: str,
    cli_args: list[str],
    editor: str,
    expected_exit_code: int,
    expected_output_fragment: str,
) -> None:
    """Tmuxp new exits with code 1 on error conditions."""
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(tmp_path))
    monkeypatch.setenv("EDITOR", editor)

    with pytest.raises(SystemExit) as exc_info:
        cli.cli(cli_args)

    assert exc_info.value.code == expected_exit_code
    if expected_output_fragment:
        captured = capsys.readouterr()
        assert expected_output_fragment in captured.out
