"""Tests for tmuxp plugin API."""

import pytest

from tmuxp.exc import TmuxpPluginException

from .fixtures.pluginsystem.partials.all_pass import AllVersionPassPlugin
from .fixtures.pluginsystem.partials.libtmux_version_fail import (
    LibtmuxVersionFailIncompatiblePlugin,
    LibtmuxVersionFailMaxPlugin,
    LibtmuxVersionFailMinPlugin,
)
from .fixtures.pluginsystem.partials.tmux_version_fail import (
    TmuxVersionFailIncompatiblePlugin,
    TmuxVersionFailMaxPlugin,
    TmuxVersionFailMinPlugin,
)
from .fixtures.pluginsystem.partials.tmuxp_version_fail import (
    TmuxpVersionFailIncompatiblePlugin,
    TmuxpVersionFailMaxPlugin,
    TmuxpVersionFailMinPlugin,
)


@pytest.fixture(autouse=True)
def autopatch_sitedir(monkeypatch_plugin_test_packages: None) -> None:
    """Fixture automatically used that patches sitedir."""


def test_all_pass() -> None:
    """Plugin for tmuxp that loads successfully."""
    AllVersionPassPlugin()


def test_tmux_version_fail_min() -> None:
    """Plugin raises if tmux version is below minimum constraint."""
    with pytest.raises(TmuxpPluginException, match=r"Incompatible.*") as exc_info:
        TmuxVersionFailMinPlugin()
    assert "tmux-min-version-fail" in str(exc_info.value)


def test_tmux_version_fail_max() -> None:
    """Plugin raises if tmux version is above maximum constraint."""
    with pytest.raises(TmuxpPluginException, match=r"Incompatible.*") as exc_info:
        TmuxVersionFailMaxPlugin()
    assert "tmux-max-version-fail" in str(exc_info.value)


def test_tmux_version_fail_incompatible() -> None:
    """Plugin raises if tmuxp version is incompatible."""
    with pytest.raises(TmuxpPluginException, match=r"Incompatible.*") as exc_info:
        TmuxVersionFailIncompatiblePlugin()
    assert "tmux-incompatible-version-fail" in str(exc_info.value)


def test_tmuxp_version_fail_min() -> None:
    """Plugin raises if tmuxp version is below minimum constraint."""
    with pytest.raises(TmuxpPluginException, match=r"Incompatible.*") as exc_info:
        TmuxpVersionFailMinPlugin()
    assert "tmuxp-min-version-fail" in str(exc_info.value)


def test_tmuxp_version_fail_max() -> None:
    """Plugin raises if tmuxp version is above max constraint."""
    with pytest.raises(TmuxpPluginException, match=r"Incompatible.*") as exc_info:
        TmuxpVersionFailMaxPlugin()
    assert "tmuxp-max-version-fail" in str(exc_info.value)


def test_tmuxp_version_fail_incompatible() -> None:
    """Plugin raises if libtmux version is below minimum constraint."""
    with pytest.raises(TmuxpPluginException, match=r"Incompatible.*") as exc_info:
        TmuxpVersionFailIncompatiblePlugin()
    assert "tmuxp-incompatible-version-fail" in str(exc_info.value)


def test_libtmux_version_fail_min() -> None:
    """Plugin raises if libtmux version is below minimum constraint."""
    with pytest.raises(TmuxpPluginException, match=r"Incompatible.*") as exc_info:
        LibtmuxVersionFailMinPlugin()
    assert "libtmux-min-version-fail" in str(exc_info.value)


def test_libtmux_version_fail_max() -> None:
    """Plugin raises if libtmux version is above max constraint."""
    with pytest.raises(TmuxpPluginException, match=r"Incompatible.*") as exc_info:
        LibtmuxVersionFailMaxPlugin()
    assert "libtmux-max-version-fail" in str(exc_info.value)


def test_libtmux_version_fail_incompatible() -> None:
    """Plugin raises if libtmux version is incompatible."""
    with pytest.raises(TmuxpPluginException, match=r"Incompatible.*") as exc_info:
        LibtmuxVersionFailIncompatiblePlugin()
    assert "libtmux-incompatible-version-fail" in str(exc_info.value)
