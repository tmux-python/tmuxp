"""Tests for freezing tmux sessions with tmuxp."""
import time

from tmuxp import config
from tmuxp.config_reader import ConfigReader
from tmuxp.workspacebuilder import WorkspaceBuilder, freeze

from .fixtures import utils as test_utils


def test_freeze_config(session):
    session_config = ConfigReader._from_file(
        test_utils.get_config_file("workspacefreezer/sampleconfig.yaml")
    )

    builder = WorkspaceBuilder(sconf=session_config)
    builder.build(session=session)
    assert session == builder.session

    time.sleep(0.50)

    session = session
    new_config = freeze(session)

    config.validate_schema(new_config)

    # These should dump without an error
    ConfigReader._dump(format="json", content=new_config)
    ConfigReader._dump(format="yaml", content=new_config)

    # Inline configs should also dump without an error
    compact_config = config.inline(new_config)

    ConfigReader._dump(format="json", content=compact_config)
    ConfigReader._dump(format="yaml", content=compact_config)
