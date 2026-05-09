"""Tests for ``tmuxp new``, ``tmuxp copy``, ``tmuxp delete``, ``tmuxp implode``."""

from __future__ import annotations

import pathlib
import typing as t

import pytest

from tmuxp.cli.manage import (
    CLICopyNamespace,
    CLIDeleteNamespace,
    CLIImplodeNamespace,
    CLINewNamespace,
    command_copy,
    command_delete,
    command_implode,
    command_new,
)

if t.TYPE_CHECKING:
    pass


@pytest.fixture
def configdir(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    """Force tmuxp config dir to a tmp_path for the test scope."""
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def no_editor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace subprocess.call with a no-op so $EDITOR doesn't actually run."""
    monkeypatch.setattr("tmuxp.cli.manage.subprocess.call", lambda *a, **kw: 0)


# ---------------------------------------------------------------------------
# new
# ---------------------------------------------------------------------------


def test_command_new_creates_file_when_missing(
    configdir: pathlib.Path, no_editor: None
) -> None:
    """`tmuxp new <name>` writes a starter YAML if file is missing."""
    args = CLINewNamespace(name="proj1", color=None)
    command_new(args)
    assert (configdir / "proj1.yaml").exists()
    content = (configdir / "proj1.yaml").read_text()
    assert "session_name: proj1" in content


def test_command_new_skips_write_when_file_exists(
    configdir: pathlib.Path, no_editor: None
) -> None:
    """`tmuxp new <name>` does not overwrite an existing file."""
    target = configdir / "proj1.yaml"
    target.write_text("session_name: original\n")
    args = CLINewNamespace(name="proj1", color=None)
    command_new(args)
    assert target.read_text() == "session_name: original\n"


# ---------------------------------------------------------------------------
# copy
# ---------------------------------------------------------------------------


def test_command_copy_duplicates_file(configdir: pathlib.Path, no_editor: None) -> None:
    """`tmuxp copy src dst` writes dst with src's content."""
    src = configdir / "src.yaml"
    src.write_text("session_name: src\n")
    args = CLICopyNamespace(src=str(src), dst="dst", answer_yes=True, color=None)
    command_copy(args)
    assert (configdir / "dst.yaml").read_text() == "session_name: src\n"


def test_command_copy_aborts_on_overwrite_decline(
    configdir: pathlib.Path,
    no_editor: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When dst exists and the user declines, dst content is preserved."""
    src = configdir / "src.yaml"
    src.write_text("session_name: src\n")
    dst = configdir / "dst.yaml"
    dst.write_text("session_name: existing\n")

    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    args = CLICopyNamespace(src=str(src), dst="dst", answer_yes=False, color=None)
    command_copy(args)
    assert dst.read_text() == "session_name: existing\n"


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_command_delete_unlinks_with_yes(
    configdir: pathlib.Path,
) -> None:
    """`tmuxp delete <name> -y` deletes without prompting."""
    target = configdir / "proj1.yaml"
    target.write_text("session_name: proj1\n")
    args = CLIDeleteNamespace(names=[str(target)], answer_yes=True, color=None)
    command_delete(args)
    assert not target.exists()


def test_command_delete_skips_missing(configdir: pathlib.Path) -> None:
    """Nonexistent name produces an error message but no exception."""
    args = CLIDeleteNamespace(
        names=["nope-no-such-config"],
        answer_yes=True,
        color=None,
    )
    command_delete(args)  # must not raise


# ---------------------------------------------------------------------------
# implode
# ---------------------------------------------------------------------------


def test_command_implode_removes_existing_dirs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """`tmuxp implode -y` removes every tmuxp config directory found."""
    legacy_dir = tmp_path / "home" / ".tmuxp"
    xdg_dir = tmp_path / "config" / "tmuxp"
    legacy_dir.mkdir(parents=True)
    xdg_dir.mkdir(parents=True)
    (legacy_dir / "p1.yaml").write_text("session_name: p1\n")
    (xdg_dir / "p2.yaml").write_text("session_name: p2\n")

    monkeypatch.setattr(
        "tmuxp.cli.manage._implode_dirs",
        lambda: [legacy_dir, xdg_dir],
    )

    args = CLIImplodeNamespace(answer_yes=True, color=None)
    command_implode(args)

    assert not legacy_dir.exists()
    assert not xdg_dir.exists()


def test_command_implode_aborts_on_decline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Declining the global confirmation leaves directories intact."""
    d = tmp_path / "tmuxp"
    d.mkdir()
    (d / "p.yaml").write_text("session_name: p\n")
    monkeypatch.setattr("tmuxp.cli.manage._implode_dirs", lambda: [d])
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    args = CLIImplodeNamespace(answer_yes=False, color=None)
    command_implode(args)
    assert d.exists()
    assert (d / "p.yaml").exists()
