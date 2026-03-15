"""Test tmuxp delete command."""

from __future__ import annotations

import typing as t

import pytest

from tmuxp import cli


class DeleteTestFixture(t.NamedTuple):
    """Test fixture for tmuxp delete command tests."""

    test_id: str
    cli_args: list[str]
    workspace_name: str
    expect_deleted: bool
    file_exists: bool


DELETE_TEST_FIXTURES: list[DeleteTestFixture] = [
    DeleteTestFixture(
        test_id="delete-workspace",
        cli_args=["delete", "-y", "target"],
        workspace_name="target",
        expect_deleted=True,
        file_exists=True,
    ),
    DeleteTestFixture(
        test_id="delete-nonexistent",
        cli_args=["delete", "-y", "nosuch"],
        workspace_name="nosuch",
        expect_deleted=False,
        file_exists=False,
    ),
]


@pytest.mark.parametrize(
    list(DeleteTestFixture._fields),
    DELETE_TEST_FIXTURES,
    ids=[test.test_id for test in DELETE_TEST_FIXTURES],
)
def test_delete(
    tmp_path: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    test_id: str,
    cli_args: list[str],
    workspace_name: str,
    expect_deleted: bool,
    file_exists: bool,
) -> None:
    """Test deleting workspace config files."""
    config_dir = tmp_path / "tmuxp"
    config_dir.mkdir()
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(config_dir))

    workspace_path = config_dir / f"{workspace_name}.yaml"
    if file_exists:
        workspace_path.write_text("session_name: target\n")

    cli.cli(cli_args)

    captured = capsys.readouterr()

    if expect_deleted:
        assert not workspace_path.exists()
        assert "Deleted" in captured.out
    else:
        assert not workspace_path.exists()
        assert "not found" in captured.out.lower()


def test_delete_multiple(
    tmp_path: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test deleting multiple workspace configs at once."""
    config_dir = tmp_path / "tmuxp"
    config_dir.mkdir()
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(config_dir))

    for name in ["proj1", "proj2"]:
        (config_dir / f"{name}.yaml").write_text(f"session_name: {name}\n")

    cli.cli(["delete", "-y", "proj1", "proj2"])

    assert not (config_dir / "proj1.yaml").exists()
    assert not (config_dir / "proj2.yaml").exists()

    captured = capsys.readouterr()
    assert captured.out.count("Deleted") == 2
