"""Tests for freezing tmux sessions with tmuxp."""
import pathlib
import time
import typing

from tmuxp.config_reader import ConfigReader
from tmuxp.workspace import freezer, validation
from tmuxp.workspace.builder import WorkspaceBuilder

from ..fixtures import utils as test_utils

if typing.TYPE_CHECKING:
    from ..fixtures.structures import WorkspaceTestData


def test_freeze_config(session):
    session_config = ConfigReader._from_file(
        test_utils.get_workspace_file("workspace/freezer/sample_workspace.yaml")
    )

    builder = WorkspaceBuilder(sconf=session_config)
    builder.build(session=session)
    assert session == builder.session

    time.sleep(0.50)

    session = session
    new_config = freezer.freeze(session)

    validation.validate_schema(new_config)

    # These should dump without an error
    ConfigReader._dump(format="json", content=new_config)
    ConfigReader._dump(format="yaml", content=new_config)

    # Inline configs should also dump without an error
    compact_config = freezer.inline(new_config)

    ConfigReader._dump(format="json", content=compact_config)
    ConfigReader._dump(format="yaml", content=compact_config)


"""Tests for :meth:`freezer.inline()`."""

ibefore_workspace = {  # inline config
    "session_name": "sample workspace",
    "start_directory": "~",
    "windows": [
        {
            "shell_command": ["top"],
            "window_name": "editor",
            "panes": [{"shell_command": ["vim"]}, {"shell_command": ['cowsay "hey"']}],
            "layout": "main-verticle",
        },
        {
            "window_name": "logging",
            "panes": [{"shell_command": ["tail -F /var/log/syslog"]}],
        },
        {"options": {"automatic-rename": True}, "panes": [{"shell_command": ["htop"]}]},
    ],
}

iafter_workspace = {
    "session_name": "sample workspace",
    "start_directory": "~",
    "windows": [
        {
            "shell_command": "top",
            "window_name": "editor",
            "panes": ["vim", 'cowsay "hey"'],
            "layout": "main-verticle",
        },
        {"window_name": "logging", "panes": ["tail -F /var/log/syslog"]},
        {"options": {"automatic-rename": True}, "panes": ["htop"]},
    ],
}


def test_inline_workspace():
    """:meth:`freezer.inline()` shell commands list to string."""

    test_workspace = freezer.inline(ibefore_workspace)
    assert test_workspace == iafter_workspace


def test_export_yaml(tmp_path: pathlib.Path, config_fixture: "WorkspaceTestData"):
    yaml_workspace_file = tmp_path / "config.yaml"

    sample_workspace = freezer.inline(
        config_fixture.sample_workspace.sample_workspace_dict
    )
    configparser = ConfigReader(sample_workspace)

    yaml_workspace_data = configparser.dump("yaml", indent=2, default_flow_style=False)

    yaml_workspace_file.write_text(yaml_workspace_data, encoding="utf-8")

    new_workspace_data = ConfigReader._from_file(yaml_workspace_file)
    assert config_fixture.sample_workspace.sample_workspace_dict == new_workspace_data
