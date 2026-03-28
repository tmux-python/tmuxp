"""Test tmuxp copy command."""

from __future__ import annotations

import pathlib
import typing as t

import pytest

from tmuxp import cli


class CopyTestFixture(t.NamedTuple):
    """Test fixture for tmuxp copy command tests."""

    test_id: str
    cli_args: list[str]
    source_name: str
    dest_name: str
    expect_copied: bool
    source_exists: bool


COPY_TEST_FIXTURES: list[CopyTestFixture] = [
    CopyTestFixture(
        test_id="copy-workspace",
        cli_args=["copy", "source", "dest"],
        source_name="source",
        dest_name="dest",
        expect_copied=True,
        source_exists=True,
    ),
    CopyTestFixture(
        test_id="copy-nonexistent-source",
        cli_args=["copy", "nosuch", "dest"],
        source_name="nosuch",
        dest_name="dest",
        expect_copied=False,
        source_exists=False,
    ),
]


@pytest.mark.parametrize(
    list(CopyTestFixture._fields),
    COPY_TEST_FIXTURES,
    ids=[test.test_id for test in COPY_TEST_FIXTURES],
)
def test_copy(
    tmp_path: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    test_id: str,
    cli_args: list[str],
    source_name: str,
    dest_name: str,
    expect_copied: bool,
    source_exists: bool,
) -> None:
    """Test copying a workspace config."""
    config_dir = tmp_path / "tmuxp"
    config_dir.mkdir()
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(config_dir))

    source_content = "session_name: source-session\nwindows:\n  - window_name: main\n"
    if source_exists:
        source_path = config_dir / f"{source_name}.yaml"
        source_path.write_text(source_content)

    if expect_copied:
        cli.cli(cli_args)

        captured = capsys.readouterr()
        dest_path = config_dir / f"{dest_name}.yaml"
        assert dest_path.exists()
        assert dest_path.read_text() == source_content
        assert "Copied" in captured.out
    else:
        with pytest.raises(SystemExit) as exc_info:
            cli.cli(cli_args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()


def test_copy_to_path(
    tmp_path: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test copying a workspace config to an explicit file path."""
    config_dir = tmp_path / "tmuxp"
    config_dir.mkdir()
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(config_dir))

    source_content = "session_name: mysession\n"
    source_path = config_dir / "source.yaml"
    source_path.write_text(source_content)

    dest_path = tmp_path / "output" / "copied.yaml"
    dest_path.parent.mkdir(parents=True)

    cli.cli(["copy", "source", str(dest_path)])

    assert dest_path.exists()
    assert dest_path.read_text() == source_content

    captured = capsys.readouterr()
    assert "Copied" in captured.out


class CopyConfigdirFixture(t.NamedTuple):
    """Fixture for TMUXP_CONFIGDIR handling in copy command."""

    test_id: str
    configdir_exists_before: bool


COPY_CONFIGDIR_FIXTURES: list[CopyConfigdirFixture] = [
    CopyConfigdirFixture(
        test_id="configdir-exists",
        configdir_exists_before=True,
    ),
    CopyConfigdirFixture(
        test_id="configdir-not-exists",
        configdir_exists_before=False,
    ),
]


@pytest.mark.parametrize(
    list(CopyConfigdirFixture._fields),
    COPY_CONFIGDIR_FIXTURES,
    ids=[f.test_id for f in COPY_CONFIGDIR_FIXTURES],
)
def test_copy_respects_tmuxp_configdir(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    configdir_exists_before: bool,
) -> None:
    """Copy lands in TMUXP_CONFIGDIR even if it doesn't exist yet."""
    # Source file in a separate directory
    source_dir = tmp_path / "source_dir"
    source_dir.mkdir()
    source_file = source_dir / "orig.yaml"
    source_file.write_text("session_name: copied\n")

    # Target configdir — may or may not exist
    config_dir = tmp_path / "custom_config"
    if configdir_exists_before:
        config_dir.mkdir()

    monkeypatch.setenv("TMUXP_CONFIGDIR", str(config_dir))

    cli.cli(["copy", str(source_file), "myworkspace"])

    expected = config_dir / "myworkspace.yaml"
    assert expected.exists(), f"expected {expected} to exist"
    assert expected.read_text() == "session_name: copied\n"


class CopyExtensionFixture(t.NamedTuple):
    """Test fixture for source extension preservation in copy."""

    test_id: str
    source_ext: str
    expected_dest_ext: str


COPY_EXTENSION_FIXTURES: list[CopyExtensionFixture] = [
    CopyExtensionFixture(
        test_id="yaml_source",
        source_ext=".yaml",
        expected_dest_ext=".yaml",
    ),
    CopyExtensionFixture(
        test_id="json_source",
        source_ext=".json",
        expected_dest_ext=".json",
    ),
    CopyExtensionFixture(
        test_id="yml_source",
        source_ext=".yml",
        expected_dest_ext=".yml",
    ),
]


@pytest.mark.parametrize(
    list(CopyExtensionFixture._fields),
    COPY_EXTENSION_FIXTURES,
    ids=[f.test_id for f in COPY_EXTENSION_FIXTURES],
)
def test_copy_preserves_source_extension(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    test_id: str,
    source_ext: str,
    expected_dest_ext: str,
) -> None:
    """Copy uses the source file extension when destination is a pure name."""
    config_dir = tmp_path / "tmuxp"
    config_dir.mkdir()
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(config_dir))

    source_content = '{"session_name": "test"}\n'
    source_path = config_dir / f"src{source_ext}"
    source_path.write_text(source_content)

    cli.cli(["copy", str(source_path), "dst"])

    expected = config_dir / f"dst{expected_dest_ext}"
    assert expected.exists(), f"expected {expected} to exist"
    assert expected.read_text() == source_content


class CopyExitCodeFixture(t.NamedTuple):
    """Test fixture for tmuxp copy error exit codes."""

    test_id: str
    cli_args: list[str]
    expected_exit_code: int
    expected_output_fragment: str


COPY_EXIT_CODE_FIXTURES: list[CopyExitCodeFixture] = [
    CopyExitCodeFixture(
        test_id="missing_source",
        cli_args=["copy", "nonexistent", "dst"],
        expected_exit_code=1,
        expected_output_fragment="Source not found",
    ),
    CopyExitCodeFixture(
        test_id="no_args",
        cli_args=["copy"],
        expected_exit_code=1,
        expected_output_fragment="",
    ),
    CopyExitCodeFixture(
        test_id="missing_destination",
        cli_args=["copy", "src"],
        expected_exit_code=1,
        expected_output_fragment="",
    ),
]


@pytest.mark.parametrize(
    list(CopyExitCodeFixture._fields),
    COPY_EXIT_CODE_FIXTURES,
    ids=[f.test_id for f in COPY_EXIT_CODE_FIXTURES],
)
def test_copy_error_exits_nonzero(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    test_id: str,
    cli_args: list[str],
    expected_exit_code: int,
    expected_output_fragment: str,
) -> None:
    """Tmuxp copy exits with code 1 on error conditions."""
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(tmp_path))

    with pytest.raises(SystemExit) as exc_info:
        cli.cli(cli_args)

    assert exc_info.value.code == expected_exit_code
    if expected_output_fragment:
        captured = capsys.readouterr()
        assert expected_output_fragment in captured.out
