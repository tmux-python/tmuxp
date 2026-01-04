"""Tests for local workspace file discovery with upward traversal."""

from __future__ import annotations

import pathlib
import typing as t

import pytest

from tmuxp.workspace.finders import LOCAL_WORKSPACE_FILES, find_local_workspace_files


class LocalWorkspaceTestFixture(t.NamedTuple):
    """Test fixture for local workspace file discovery."""

    test_id: str
    files: dict[str, str]  # {dir_relative_to_home: filename}
    start_dir: str  # relative to home
    expected_count: int
    expected_paths: list[str]  # relative to home


LOCAL_WORKSPACE_TEST_FIXTURES: list[LocalWorkspaceTestFixture] = [
    LocalWorkspaceTestFixture(
        test_id="only_in_cwd",
        files={"project": ".tmuxp.yaml"},
        start_dir="project",
        expected_count=1,
        expected_paths=["project/.tmuxp.yaml"],
    ),
    LocalWorkspaceTestFixture(
        test_id="only_in_parent",
        files={"project": ".tmuxp.yaml"},
        start_dir="project/subdir",
        expected_count=1,
        expected_paths=["project/.tmuxp.yaml"],
    ),
    LocalWorkspaceTestFixture(
        test_id="in_cwd_and_parent",
        files={
            "project": ".tmuxp.yaml",
            "project/subdir": ".tmuxp.yaml",
        },
        start_dir="project/subdir",
        expected_count=2,
        expected_paths=["project/subdir/.tmuxp.yaml", "project/.tmuxp.yaml"],
    ),
    LocalWorkspaceTestFixture(
        test_id="multiple_ancestors",
        files={
            "a": ".tmuxp.yaml",
            "a/b": ".tmuxp.yaml",
            "a/b/c": ".tmuxp.yaml",
        },
        start_dir="a/b/c/d",
        expected_count=3,
        expected_paths=[
            "a/b/c/.tmuxp.yaml",
            "a/b/.tmuxp.yaml",
            "a/.tmuxp.yaml",
        ],
    ),
    LocalWorkspaceTestFixture(
        test_id="no_local_files",
        files={},
        start_dir="project",
        expected_count=0,
        expected_paths=[],
    ),
    LocalWorkspaceTestFixture(
        test_id="json_format",
        files={"project": ".tmuxp.json"},
        start_dir="project",
        expected_count=1,
        expected_paths=["project/.tmuxp.json"],
    ),
    LocalWorkspaceTestFixture(
        test_id="yml_format",
        files={"project": ".tmuxp.yml"},
        start_dir="project",
        expected_count=1,
        expected_paths=["project/.tmuxp.yml"],
    ),
    LocalWorkspaceTestFixture(
        test_id="stops_at_home",
        files={
            "": ".tmuxp.yaml",  # In home dir itself
            "project": ".tmuxp.yaml",
        },
        start_dir="project",
        expected_count=2,  # Includes home but stops there
        expected_paths=["project/.tmuxp.yaml", ".tmuxp.yaml"],
    ),
]


@pytest.mark.parametrize(
    LocalWorkspaceTestFixture._fields,
    LOCAL_WORKSPACE_TEST_FIXTURES,
    ids=[test.test_id for test in LOCAL_WORKSPACE_TEST_FIXTURES],
)
def test_find_local_workspace_files(
    test_id: str,
    files: dict[str, str],
    start_dir: str,
    expected_count: int,
    expected_paths: list[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test local workspace file discovery with upward traversal."""
    home = tmp_path / "home"
    home.mkdir()

    # Create directory structure and files
    for rel_dir, filename in files.items():
        dir_path = home / rel_dir if rel_dir else home
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / filename).write_text("session_name: test\n")

    # Ensure start directory exists
    start_path = home / start_dir
    start_path.mkdir(parents=True, exist_ok=True)

    # Mock home directory
    monkeypatch.setattr(pathlib.Path, "home", lambda: home)

    # Run the function
    result = find_local_workspace_files(start_path, stop_at_home=True)

    assert len(result) == expected_count

    # Verify paths match expected (relative to home)
    result_relative = [str(p.relative_to(home)) for p in result]
    assert result_relative == expected_paths


class TestFindLocalWorkspaceEdgeCases:
    """Edge case tests for local workspace discovery."""

    def test_at_home_directory(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test behavior when starting at home directory."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setattr(pathlib.Path, "home", lambda: home)

        (home / ".tmuxp.yaml").write_text("session_name: home\n")

        result = find_local_workspace_files(home, stop_at_home=True)

        assert len(result) == 1
        assert result[0] == home / ".tmuxp.yaml"

    def test_at_filesystem_root(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test traversal stops at filesystem root."""
        # This test verifies no infinite loop at root
        result = find_local_workspace_files(pathlib.Path("/"), stop_at_home=False)
        # Should complete without error; result depends on system state
        assert isinstance(result, list)

    def test_yaml_precedence_over_json(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test .yaml is preferred when multiple formats exist."""
        home = tmp_path / "home"
        project = home / "project"
        project.mkdir(parents=True)
        monkeypatch.setattr(pathlib.Path, "home", lambda: home)

        # Create both formats
        (project / ".tmuxp.yaml").write_text("session_name: yaml\n")
        (project / ".tmuxp.json").write_text('{"session_name": "json"}')

        result = find_local_workspace_files(project, stop_at_home=True)

        assert len(result) == 1
        assert result[0].name == ".tmuxp.yaml"

    def test_yml_precedence_over_json(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test .yml is preferred when .yaml not present but .json exists."""
        home = tmp_path / "home"
        project = home / "project"
        project.mkdir(parents=True)
        monkeypatch.setattr(pathlib.Path, "home", lambda: home)

        # Create yml and json (no yaml)
        (project / ".tmuxp.yml").write_text("session_name: yml\n")
        (project / ".tmuxp.json").write_text('{"session_name": "json"}')

        result = find_local_workspace_files(project, stop_at_home=True)

        assert len(result) == 1
        assert result[0].name == ".tmuxp.yml"

    def test_stop_at_home_false_continues_past_home(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test stop_at_home=False continues traversal past home."""
        # Create structure: /grandparent/home/project
        grandparent = tmp_path / "grandparent"
        home = grandparent / "home"
        project = home / "project"
        project.mkdir(parents=True)

        monkeypatch.setattr(pathlib.Path, "home", lambda: home)

        # Put config in grandparent (above home)
        (grandparent / ".tmuxp.yaml").write_text("session_name: grandparent\n")
        (project / ".tmuxp.yaml").write_text("session_name: project\n")

        # With stop_at_home=True, should only find project config
        result_stop = find_local_workspace_files(project, stop_at_home=True)
        assert len(result_stop) == 1
        assert "project" in str(result_stop[0])

        # With stop_at_home=False, should find both
        result_continue = find_local_workspace_files(project, stop_at_home=False)
        assert len(result_continue) >= 2

    def test_default_start_dir_uses_cwd(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that None start_dir uses current working directory."""
        home = tmp_path / "home"
        project = home / "project"
        project.mkdir(parents=True)
        monkeypatch.setattr(pathlib.Path, "home", lambda: home)
        monkeypatch.chdir(project)

        (project / ".tmuxp.yaml").write_text("session_name: cwd\n")

        result = find_local_workspace_files(None, stop_at_home=True)

        assert len(result) == 1
        assert result[0] == project / ".tmuxp.yaml"

    def test_symlinked_directory(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test behavior with symlinked directories."""
        home = tmp_path / "home"
        real_project = home / "real_project"
        real_project.mkdir(parents=True)
        symlink_project = home / "symlink_project"
        symlink_project.symlink_to(real_project)
        monkeypatch.setattr(pathlib.Path, "home", lambda: home)

        (real_project / ".tmuxp.yaml").write_text("session_name: test\n")

        result = find_local_workspace_files(symlink_project, stop_at_home=True)

        assert len(result) == 1


class TestLocalWorkspaceFilesConstant:
    """Tests for LOCAL_WORKSPACE_FILES constant."""

    def test_constant_order(self) -> None:
        """Verify LOCAL_WORKSPACE_FILES has correct order (yaml, yml, json)."""
        assert LOCAL_WORKSPACE_FILES == [".tmuxp.yaml", ".tmuxp.yml", ".tmuxp.json"]

    def test_constant_is_list(self) -> None:
        """Verify LOCAL_WORKSPACE_FILES is a list."""
        assert isinstance(LOCAL_WORKSPACE_FILES, list)
        assert len(LOCAL_WORKSPACE_FILES) == 3
