"""CLI tests for tmuxp ls command."""

import contextlib
import pathlib

import pytest

from tmuxp import cli


def test_ls_cli(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI test for tmuxp ls."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))

    filenames = [
        ".git/",
        ".gitignore/",
        "session_1.yaml",
        "session_2.yaml",
        "session_3.json",
        "session_4.txt",
    ]

    # should ignore:
    # - directories should be ignored
    # - extensions not covered in VALID_WORKSPACE_DIR_FILE_EXTENSIONS
    ignored_filenames = [".git/", ".gitignore/", "session_4.txt"]
    stems = [pathlib.Path(f).stem for f in filenames if f not in ignored_filenames]

    for filename in filenames:
        location = tmp_path / f".tmuxp/{filename}"
        if filename.endswith("/"):
            location.mkdir(parents=True)
        else:
            location.touch()

    with contextlib.suppress(SystemExit):
        cli.cli(["ls"])

    cli_output = capsys.readouterr().out

    assert cli_output == "\n".join(stems) + "\n"
