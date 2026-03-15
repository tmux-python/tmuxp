"""Test tmuxp new command."""

from __future__ import annotations

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
