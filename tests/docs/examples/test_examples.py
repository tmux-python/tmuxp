"""Tests for example workspace YAML files."""

from __future__ import annotations

import functools

from libtmux.pane import Pane
from libtmux.session import Session
from libtmux.test.retry import retry_until

from tests.constants import EXAMPLE_PATH
from tmuxp._internal.config_reader import ConfigReader
from tmuxp.workspace import loader
from tmuxp.workspace.builder import WorkspaceBuilder


def test_synchronize_shorthand(session: Session) -> None:
    """Test synchronize-shorthand.yaml builds and sets synchronize-panes."""
    config = ConfigReader._from_file(EXAMPLE_PATH / "synchronize-shorthand.yaml")
    config = loader.expand(config)
    builder = WorkspaceBuilder(session_config=config, server=session.server)
    builder.build(session=session)

    windows = session.windows
    assert len(windows) == 3

    synced_before = windows[0]
    synced_after = windows[1]
    not_synced = windows[2]

    assert synced_before.show_option("synchronize-panes") is True
    assert synced_after.show_option("synchronize-panes") is True
    assert not_synced.show_option("synchronize-panes") is not True


def test_lifecycle_hooks(session: Session) -> None:
    """Test lifecycle-hooks.yaml loads without error."""
    config = ConfigReader._from_file(EXAMPLE_PATH / "lifecycle-hooks.yaml")
    config = loader.expand(config)
    builder = WorkspaceBuilder(session_config=config, server=session.server)
    builder.build(session=session)

    assert len(session.windows) >= 1


def test_config_templating(session: Session) -> None:
    """Test config-templating.yaml renders templates and builds."""
    config = ConfigReader._from_file(
        EXAMPLE_PATH / "config-templating.yaml",
        template_context={"project": "myapp"},
    )
    config = loader.expand(config)

    assert config["session_name"] == "myapp"
    assert config["windows"][0]["window_name"] == "myapp-main"

    builder = WorkspaceBuilder(session_config=config, server=session.server)
    builder.build(session=session)

    assert len(session.windows) >= 1


def test_pane_titles(session: Session) -> None:
    """Test pane-titles.yaml builds with pane title options."""
    config = ConfigReader._from_file(EXAMPLE_PATH / "pane-titles.yaml")
    config = loader.expand(config)
    builder = WorkspaceBuilder(session_config=config, server=session.server)
    builder.build(session=session)

    window = session.windows[0]
    assert window.show_option("pane-border-status") == "top"
    assert window.show_option("pane-border-format") == "#{pane_index}: #{pane_title}"

    panes = window.panes
    assert len(panes) == 3

    def check_title(p: Pane, expected: str) -> bool:
        p.refresh()
        return p.pane_title == expected

    assert retry_until(
        functools.partial(check_title, panes[0], "editor"),
    ), f"Expected title 'editor', got '{panes[0].pane_title}'"
    assert retry_until(
        functools.partial(check_title, panes[1], "runner"),
    ), f"Expected title 'runner', got '{panes[1].pane_title}'"
