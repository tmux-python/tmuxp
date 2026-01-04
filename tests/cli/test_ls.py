"""CLI tests for tmuxp ls command."""

from __future__ import annotations

import contextlib
import json
import pathlib

import pytest

from tmuxp import cli
from tmuxp.cli._output import OutputMode, get_output_mode
from tmuxp.cli.ls import (
    _get_workspace_info,
    create_ls_subparser,
)


class TestGetOutputMode:
    """Tests for output mode determination."""

    def test_default_is_human(self) -> None:
        """Default mode should be HUMAN when no flags."""
        assert get_output_mode(json_flag=False, ndjson_flag=False) == OutputMode.HUMAN

    def test_json_flag(self) -> None:
        """JSON flag should return JSON mode."""
        assert get_output_mode(json_flag=True, ndjson_flag=False) == OutputMode.JSON

    def test_ndjson_flag(self) -> None:
        """NDJSON flag should return NDJSON mode."""
        assert get_output_mode(json_flag=False, ndjson_flag=True) == OutputMode.NDJSON

    def test_ndjson_takes_precedence(self) -> None:
        """NDJSON should take precedence when both flags set."""
        assert get_output_mode(json_flag=True, ndjson_flag=True) == OutputMode.NDJSON


class TestWorkspaceInfo:
    """Tests for workspace info extraction."""

    def test_get_workspace_info_yaml(self, tmp_path: pathlib.Path) -> None:
        """Extract metadata from YAML workspace file."""
        workspace = tmp_path / "test.yaml"
        workspace.write_text("session_name: my-session\nwindows: []")

        info = _get_workspace_info(workspace)

        assert info["name"] == "test"
        assert info["format"] == "yaml"
        assert info["session_name"] == "my-session"
        assert info["size"] > 0
        assert "T" in info["mtime"]  # ISO format contains T

    def test_get_workspace_info_json(self, tmp_path: pathlib.Path) -> None:
        """Extract metadata from JSON workspace file."""
        workspace = tmp_path / "test.json"
        workspace.write_text('{"session_name": "json-session", "windows": []}')

        info = _get_workspace_info(workspace)

        assert info["name"] == "test"
        assert info["format"] == "json"
        assert info["session_name"] == "json-session"

    def test_get_workspace_info_no_session_name(self, tmp_path: pathlib.Path) -> None:
        """Handle workspace without session_name."""
        workspace = tmp_path / "test.yaml"
        workspace.write_text("windows: []")

        info = _get_workspace_info(workspace)

        assert info["name"] == "test"
        assert info["session_name"] is None

    def test_get_workspace_info_invalid_yaml(self, tmp_path: pathlib.Path) -> None:
        """Handle invalid YAML gracefully."""
        workspace = tmp_path / "test.yaml"
        workspace.write_text("{{{{invalid yaml")

        info = _get_workspace_info(workspace)

        assert info["name"] == "test"
        assert info["session_name"] is None  # Couldn't parse, so None


class TestLsSubparser:
    """Tests for ls subparser configuration."""

    def test_create_ls_subparser_adds_tree_flag(self) -> None:
        """Verify --tree argument is added."""
        import argparse

        parser = argparse.ArgumentParser()
        create_ls_subparser(parser)
        args = parser.parse_args(["--tree"])

        assert args.tree is True

    def test_create_ls_subparser_adds_json_flag(self) -> None:
        """Verify --json argument is added."""
        import argparse

        parser = argparse.ArgumentParser()
        create_ls_subparser(parser)
        args = parser.parse_args(["--json"])

        assert args.output_json is True

    def test_create_ls_subparser_adds_ndjson_flag(self) -> None:
        """Verify --ndjson argument is added."""
        import argparse

        parser = argparse.ArgumentParser()
        create_ls_subparser(parser)
        args = parser.parse_args(["--ndjson"])

        assert args.output_ndjson is True


class TestLsCli:
    """CLI integration tests for tmuxp ls."""

    def test_ls_cli(
        self,
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

    def test_ls_json_output(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """CLI test for tmuxp ls --json."""
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
        monkeypatch.delenv("NO_COLOR", raising=False)

        tmuxp_dir = tmp_path / ".tmuxp"
        tmuxp_dir.mkdir(parents=True)
        (tmuxp_dir / "dev.yaml").write_text("session_name: development\nwindows: []")
        (tmuxp_dir / "prod.json").write_text('{"session_name": "production"}')

        with contextlib.suppress(SystemExit):
            cli.cli(["ls", "--json"])

        output = capsys.readouterr().out
        data = json.loads(output)

        assert isinstance(data, list)
        assert len(data) == 2

        names = {item["name"] for item in data}
        assert names == {"dev", "prod"}

        # Verify all expected fields are present
        for item in data:
            assert "name" in item
            assert "path" in item
            assert "format" in item
            assert "size" in item
            assert "mtime" in item
            assert "session_name" in item

    def test_ls_ndjson_output(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """CLI test for tmuxp ls --ndjson."""
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
        monkeypatch.delenv("NO_COLOR", raising=False)

        tmuxp_dir = tmp_path / ".tmuxp"
        tmuxp_dir.mkdir(parents=True)
        (tmuxp_dir / "ws1.yaml").write_text("session_name: s1\nwindows: []")
        (tmuxp_dir / "ws2.yaml").write_text("session_name: s2\nwindows: []")

        with contextlib.suppress(SystemExit):
            cli.cli(["ls", "--ndjson"])

        output = capsys.readouterr().out
        lines = [line for line in output.strip().split("\n") if line]

        assert len(lines) == 2

        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert "name" in data
            assert "session_name" in data

    def test_ls_tree_output(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """CLI test for tmuxp ls --tree."""
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
        monkeypatch.delenv("NO_COLOR", raising=False)

        tmuxp_dir = tmp_path / ".tmuxp"
        tmuxp_dir.mkdir(parents=True)
        (tmuxp_dir / "dev.yaml").write_text("session_name: development\nwindows: []")

        with contextlib.suppress(SystemExit):
            cli.cli(["--color=never", "ls", "--tree"])

        output = capsys.readouterr().out

        # Tree mode shows directory header
        assert "~/.tmuxp" in output
        # And indented workspace name
        assert "dev" in output

    def test_ls_empty_directory(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """CLI test for tmuxp ls with no workspaces."""
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
        monkeypatch.delenv("NO_COLOR", raising=False)

        tmuxp_dir = tmp_path / ".tmuxp"
        tmuxp_dir.mkdir(parents=True)

        with contextlib.suppress(SystemExit):
            cli.cli(["--color=never", "ls"])

        output = capsys.readouterr().out
        assert "No workspaces found" in output

    def test_ls_tree_shows_session_name_if_different(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Tree mode shows session_name if it differs from file name."""
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
        monkeypatch.delenv("NO_COLOR", raising=False)

        tmuxp_dir = tmp_path / ".tmuxp"
        tmuxp_dir.mkdir(parents=True)
        # File named "myfile" but session is "actual-session"
        (tmuxp_dir / "myfile.yaml").write_text(
            "session_name: actual-session\nwindows: []"
        )

        with contextlib.suppress(SystemExit):
            cli.cli(["--color=never", "ls", "--tree"])

        output = capsys.readouterr().out

        assert "myfile" in output
        assert "actual-session" in output
