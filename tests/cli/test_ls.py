"""CLI tests for tmuxp ls command."""

from __future__ import annotations

import contextlib
import json
import pathlib

import pytest

from tmuxp import cli
from tmuxp.cli.ls import (
    _get_workspace_info,
    create_ls_subparser,
)


def test_get_workspace_info_yaml(tmp_path: pathlib.Path) -> None:
    """Extract metadata from YAML workspace file."""
    workspace = tmp_path / "test.yaml"
    workspace.write_text("session_name: my-session\nwindows: []")

    info = _get_workspace_info(workspace)

    assert info["name"] == "test"
    assert info["format"] == "yaml"
    assert info["session_name"] == "my-session"
    assert info["size"] > 0
    assert "T" in info["mtime"]  # ISO format contains T
    assert info["source"] == "global"  # Default source


def test_get_workspace_info_source_local(tmp_path: pathlib.Path) -> None:
    """Extract metadata with source=local."""
    workspace = tmp_path / ".tmuxp.yaml"
    workspace.write_text("session_name: local-session\nwindows: []")

    info = _get_workspace_info(workspace, source="local")

    assert info["name"] == ".tmuxp"
    assert info["source"] == "local"
    assert info["session_name"] == "local-session"


def test_get_workspace_info_json(tmp_path: pathlib.Path) -> None:
    """Extract metadata from JSON workspace file."""
    workspace = tmp_path / "test.json"
    workspace.write_text('{"session_name": "json-session", "windows": []}')

    info = _get_workspace_info(workspace)

    assert info["name"] == "test"
    assert info["format"] == "json"
    assert info["session_name"] == "json-session"


def test_get_workspace_info_no_session_name(tmp_path: pathlib.Path) -> None:
    """Handle workspace without session_name."""
    workspace = tmp_path / "test.yaml"
    workspace.write_text("windows: []")

    info = _get_workspace_info(workspace)

    assert info["name"] == "test"
    assert info["session_name"] is None


def test_get_workspace_info_invalid_yaml(tmp_path: pathlib.Path) -> None:
    """Handle invalid YAML gracefully."""
    workspace = tmp_path / "test.yaml"
    workspace.write_text("{{{{invalid yaml")

    info = _get_workspace_info(workspace)

    assert info["name"] == "test"
    assert info["session_name"] is None  # Couldn't parse, so None


def test_ls_subparser_adds_tree_flag() -> None:
    """Verify --tree argument is added."""
    import argparse

    parser = argparse.ArgumentParser()
    create_ls_subparser(parser)
    args = parser.parse_args(["--tree"])

    assert args.tree is True


def test_ls_subparser_adds_json_flag() -> None:
    """Verify --json argument is added."""
    import argparse

    parser = argparse.ArgumentParser()
    create_ls_subparser(parser)
    args = parser.parse_args(["--json"])

    assert args.output_json is True


def test_ls_subparser_adds_ndjson_flag() -> None:
    """Verify --ndjson argument is added."""
    import argparse

    parser = argparse.ArgumentParser()
    create_ls_subparser(parser)
    args = parser.parse_args(["--ndjson"])

    assert args.output_ndjson is True


def test_ls_cli(
    isolated_home: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI test for tmuxp ls."""
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
        location = isolated_home / f".tmuxp/{filename}"
        if filename.endswith("/"):
            location.mkdir(parents=True)
        else:
            location.touch()

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls"])

    cli_output = capsys.readouterr().out

    # Output now has headers with directory path, check for workspace names
    assert "Global workspaces (~/.tmuxp):" in cli_output
    for stem in stems:
        assert stem in cli_output


def test_ls_json_output(
    isolated_home: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI test for tmuxp ls --json."""
    tmuxp_dir = isolated_home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)
    (tmuxp_dir / "dev.yaml").write_text("session_name: development\nwindows: []")
    (tmuxp_dir / "prod.json").write_text('{"session_name": "production"}')

    with contextlib.suppress(SystemExit):
        cli.cli(["ls", "--json"])

    output = capsys.readouterr().out
    data = json.loads(output)

    # JSON output is now an object with workspaces and global_workspace_dirs
    assert isinstance(data, dict)
    assert "workspaces" in data
    assert "global_workspace_dirs" in data

    workspaces = data["workspaces"]
    assert len(workspaces) == 2

    names = {item["name"] for item in workspaces}
    assert names == {"dev", "prod"}

    # Verify all expected fields are present
    for item in workspaces:
        assert "name" in item
        assert "path" in item
        assert "format" in item
        assert "size" in item
        assert "mtime" in item
        assert "session_name" in item
        assert "source" in item
        assert item["source"] == "global"


def test_ls_ndjson_output(
    isolated_home: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI test for tmuxp ls --ndjson."""
    tmuxp_dir = isolated_home / ".tmuxp"
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
        assert "source" in data


def test_ls_tree_output(
    isolated_home: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI test for tmuxp ls --tree."""
    tmuxp_dir = isolated_home / ".tmuxp"
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
    isolated_home: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI test for tmuxp ls with no workspaces."""
    tmuxp_dir = isolated_home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls"])

    output = capsys.readouterr().out
    assert "No workspaces found" in output


def test_ls_tree_shows_session_name_if_different(
    isolated_home: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Tree mode shows session_name if it differs from file name."""
    tmuxp_dir = isolated_home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)
    # File named "myfile" but session is "actual-session"
    (tmuxp_dir / "myfile.yaml").write_text("session_name: actual-session\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls", "--tree"])

    output = capsys.readouterr().out

    assert "myfile" in output
    assert "actual-session" in output


def test_ls_finds_local_workspace_in_cwd(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ls should find .tmuxp.yaml in current directory."""
    home = tmp_path / "home"
    project = home / "project"
    project.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(project)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)

    (project / ".tmuxp.yaml").write_text("session_name: local\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls"])

    output = capsys.readouterr().out
    assert "Local workspaces:" in output
    assert ".tmuxp" in output


def test_ls_finds_local_workspace_in_parent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ls should find .tmuxp.yaml in parent directory."""
    home = tmp_path / "home"
    project = home / "project"
    subdir = project / "src" / "module"
    subdir.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(subdir)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)

    (project / ".tmuxp.yaml").write_text("session_name: parent-local\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls"])

    output = capsys.readouterr().out
    assert "Local workspaces:" in output
    assert ".tmuxp" in output


def test_ls_shows_local_and_global(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ls should show both local and global workspaces."""
    home = tmp_path / "home"
    project = home / "project"
    project.mkdir(parents=True)
    tmuxp_dir = home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(project)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)

    # Local workspace
    (project / ".tmuxp.yaml").write_text("session_name: local\nwindows: []")
    # Global workspace
    (tmuxp_dir / "global.yaml").write_text("session_name: global\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls"])

    output = capsys.readouterr().out
    assert "Local workspaces:" in output
    assert "Global workspaces (~/.tmuxp):" in output
    assert ".tmuxp" in output
    assert "global" in output


def test_ls_json_includes_source_for_local(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON output should include source=local for local workspaces."""
    home = tmp_path / "home"
    project = home / "project"
    project.mkdir(parents=True)
    tmuxp_dir = home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(project)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)

    (project / ".tmuxp.yaml").write_text("session_name: local\nwindows: []")
    (tmuxp_dir / "global.yaml").write_text("session_name: global\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["ls", "--json"])

    output = capsys.readouterr().out
    data = json.loads(output)

    # JSON output is now an object with workspaces and global_workspace_dirs
    assert isinstance(data, dict)
    workspaces = data["workspaces"]

    sources = {item["source"] for item in workspaces}
    assert sources == {"local", "global"}

    local_items = [item for item in workspaces if item["source"] == "local"]
    global_items = [item for item in workspaces if item["source"] == "global"]

    assert len(local_items) == 1
    assert len(global_items) == 1
    assert local_items[0]["session_name"] == "local"
    assert global_items[0]["session_name"] == "global"


def test_ls_local_shows_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Local workspaces should show their path in flat mode."""
    home = tmp_path / "home"
    project = home / "project"
    project.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(project)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)

    (project / ".tmuxp.yaml").write_text("session_name: local\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls"])

    output = capsys.readouterr().out
    # Local workspace output shows path (with ~ contraction)
    assert "~/project/.tmuxp.yaml" in output


def test_ls_full_flag_subparser() -> None:
    """Verify --full argument is added to subparser."""
    import argparse

    from tmuxp.cli.ls import create_ls_subparser

    parser = argparse.ArgumentParser()
    create_ls_subparser(parser)
    args = parser.parse_args(["--full"])

    assert args.full is True


def test_get_workspace_info_include_config(tmp_path: pathlib.Path) -> None:
    """Test _get_workspace_info with include_config=True."""
    workspace = tmp_path / "test.yaml"
    workspace.write_text("session_name: test\nwindows:\n  - window_name: editor\n")

    info = _get_workspace_info(workspace, include_config=True)

    assert "config" in info
    assert info["config"]["session_name"] == "test"
    assert len(info["config"]["windows"]) == 1


def test_get_workspace_info_no_config_by_default(tmp_path: pathlib.Path) -> None:
    """Test _get_workspace_info without include_config doesn't include config."""
    workspace = tmp_path / "test.yaml"
    workspace.write_text("session_name: test\nwindows: []\n")

    info = _get_workspace_info(workspace)

    assert "config" not in info


def test_ls_json_full_includes_config(
    isolated_home: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON output with --full includes config content."""
    tmuxp_dir = isolated_home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)
    (tmuxp_dir / "dev.yaml").write_text(
        "session_name: dev\n"
        "windows:\n"
        "  - window_name: editor\n"
        "    panes:\n"
        "      - vim\n"
    )

    with contextlib.suppress(SystemExit):
        cli.cli(["ls", "--json", "--full"])

    output = capsys.readouterr().out
    data = json.loads(output)

    # JSON output is now an object with workspaces and global_workspace_dirs
    assert isinstance(data, dict)
    workspaces = data["workspaces"]

    assert len(workspaces) == 1
    assert "config" in workspaces[0]
    assert workspaces[0]["config"]["session_name"] == "dev"
    assert workspaces[0]["config"]["windows"][0]["window_name"] == "editor"


def test_ls_full_tree_shows_windows(
    isolated_home: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Tree mode with --full shows window/pane hierarchy."""
    tmuxp_dir = isolated_home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)
    (tmuxp_dir / "dev.yaml").write_text(
        "session_name: dev\n"
        "windows:\n"
        "  - window_name: editor\n"
        "    layout: main-horizontal\n"
        "    panes:\n"
        "      - vim\n"
        "  - window_name: shell\n"
    )

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls", "--tree", "--full"])

    output = capsys.readouterr().out

    assert "dev" in output
    assert "editor" in output
    assert "main-horizontal" in output
    assert "shell" in output
    assert "pane 0" in output


def test_ls_full_flat_shows_windows(
    isolated_home: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Flat mode with --full shows window/pane hierarchy."""
    tmuxp_dir = isolated_home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)
    (tmuxp_dir / "dev.yaml").write_text(
        "session_name: dev\nwindows:\n  - window_name: code\n    panes:\n      - nvim\n"
    )

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls", "--full"])

    output = capsys.readouterr().out

    assert "Global workspaces (~/.tmuxp):" in output
    assert "dev" in output
    assert "code" in output
    assert "pane 0" in output


def test_ls_full_without_json_no_config_in_output(
    isolated_home: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Non-JSON with --full shows tree but not raw config."""
    tmuxp_dir = isolated_home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)
    (tmuxp_dir / "dev.yaml").write_text(
        "session_name: dev\nwindows:\n  - window_name: editor\n"
    )

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls", "--full"])

    output = capsys.readouterr().out

    # Should show tree structure, not raw config keys
    assert "editor" in output
    assert "session_name:" not in output  # Raw YAML not in output


def test_ls_shows_global_workspace_dirs_section(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Human output shows global workspace directories section."""
    home = tmp_path / "home"
    tmuxp_dir = home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(home)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)
    monkeypatch.delenv("TMUXP_CONFIGDIR", raising=False)

    (tmuxp_dir / "workspace.yaml").write_text("session_name: test\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls"])

    output = capsys.readouterr().out

    assert "Global workspace directories:" in output
    assert "Legacy: ~/.tmuxp" in output
    assert "1 workspace" in output
    assert "active" in output
    assert "~/.config/tmuxp" in output
    assert "not found" in output


def test_ls_global_header_shows_active_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Global workspaces header shows active directory path."""
    home = tmp_path / "home"
    tmuxp_dir = home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(home)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)
    monkeypatch.delenv("TMUXP_CONFIGDIR", raising=False)

    (tmuxp_dir / "workspace.yaml").write_text("session_name: test\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls"])

    output = capsys.readouterr().out

    # Header should include the active directory
    assert "Global workspaces (~/.tmuxp):" in output


def test_ls_json_includes_global_workspace_dirs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON output includes global_workspace_dirs array."""
    home = tmp_path / "home"
    tmuxp_dir = home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(home)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)
    monkeypatch.delenv("TMUXP_CONFIGDIR", raising=False)

    (tmuxp_dir / "workspace.yaml").write_text("session_name: test\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["ls", "--json"])

    output = capsys.readouterr().out
    data = json.loads(output)

    # JSON should be an object with workspaces and global_workspace_dirs
    assert isinstance(data, dict)
    assert "workspaces" in data
    assert "global_workspace_dirs" in data

    # Check global_workspace_dirs structure
    dirs = data["global_workspace_dirs"]
    assert isinstance(dirs, list)
    assert len(dirs) >= 1

    for d in dirs:
        assert "path" in d
        assert "source" in d
        assert "exists" in d
        assert "workspace_count" in d
        assert "active" in d

    # Find the active one
    active_dirs = [d for d in dirs if d["active"]]
    assert len(active_dirs) == 1
    assert active_dirs[0]["path"] == "~/.tmuxp"
    assert active_dirs[0]["exists"] is True
    assert active_dirs[0]["workspace_count"] == 1


def test_ls_json_empty_still_has_global_workspace_dirs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON output with no workspaces still includes global_workspace_dirs."""
    home = tmp_path / "home"
    tmuxp_dir = home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)  # Empty directory

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(home)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)
    monkeypatch.delenv("TMUXP_CONFIGDIR", raising=False)

    with contextlib.suppress(SystemExit):
        cli.cli(["ls", "--json"])

    output = capsys.readouterr().out
    data = json.loads(output)

    assert "workspaces" in data
    assert "global_workspace_dirs" in data
    assert len(data["workspaces"]) == 0
    assert len(data["global_workspace_dirs"]) >= 1


def test_ls_xdg_takes_precedence_in_header(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When XDG dir exists, it shows in header instead of ~/.tmuxp."""
    home = tmp_path / "home"
    xdg_tmuxp = home / ".config" / "tmuxp"
    xdg_tmuxp.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(home)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)
    monkeypatch.delenv("TMUXP_CONFIGDIR", raising=False)

    (xdg_tmuxp / "workspace.yaml").write_text("session_name: test\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls"])

    output = capsys.readouterr().out

    # Header should show XDG path when it's active
    assert "Global workspaces (~/.config/tmuxp):" in output


def test_ls_tree_shows_global_workspace_dirs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Tree mode also shows global workspace directories section."""
    home = tmp_path / "home"
    tmuxp_dir = home / ".tmuxp"
    tmuxp_dir.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(home)
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)
    monkeypatch.delenv("TMUXP_CONFIGDIR", raising=False)

    (tmuxp_dir / "workspace.yaml").write_text("session_name: test\nwindows: []")

    with contextlib.suppress(SystemExit):
        cli.cli(["--color=never", "ls", "--tree"])

    output = capsys.readouterr().out

    assert "Global workspace directories:" in output
    assert "Legacy: ~/.tmuxp" in output
    assert "active" in output
