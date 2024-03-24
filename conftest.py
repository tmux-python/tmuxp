"""Conftest.py (root-level).

We keep this in root pytest fixtures in pytest's doctest plugin to be available, as well
as avoiding conftest.py from being included in the wheel, in addition to pytest_plugin
for pytester only being available via the root directory.

See "pytest_plugins in non-top-level conftest files" in
https://docs.pytest.org/en/stable/deprecations.html
"""

import logging
import os
import pathlib
import shutil
import typing as t

import pytest
from _pytest.doctest import DoctestItem
from libtmux.test import namer

from tests.fixtures import utils as test_utils
from tmuxp.workspace.finders import get_workspace_dir

if t.TYPE_CHECKING:
    from libtmux.session import Session

logger = logging.getLogger(__name__)
USING_ZSH = "zsh" in os.getenv("SHELL", "")


@pytest.fixture(autouse=USING_ZSH, scope="session")
def zshrc(user_path: pathlib.Path) -> t.Optional[pathlib.Path]:
    """Quiets ZSH default message.

    Needs a startup file .zshenv, .zprofile, .zshrc, .zlogin.
    """
    if not USING_ZSH:
        return None
    p = user_path / ".zshrc"
    p.touch()
    return p


@pytest.fixture(autouse=True)
def home_path_default(monkeypatch: pytest.MonkeyPatch, user_path: pathlib.Path) -> None:
    """Set HOME to user_path (random, temporary directory)."""
    monkeypatch.setenv("HOME", str(user_path))


@pytest.fixture()
def tmuxp_configdir(user_path: pathlib.Path) -> pathlib.Path:
    """Ensure and return tmuxp config directory."""
    xdg_config_dir = user_path / ".config"
    xdg_config_dir.mkdir(exist_ok=True)

    tmuxp_configdir = xdg_config_dir / "tmuxp"
    tmuxp_configdir.mkdir(exist_ok=True)
    return tmuxp_configdir


@pytest.fixture()
def tmuxp_configdir_default(
    monkeypatch: pytest.MonkeyPatch,
    tmuxp_configdir: pathlib.Path,
) -> None:
    """Set tmuxp configuration directory for ``TMUXP_CONFIGDIR``."""
    monkeypatch.setenv("TMUXP_CONFIGDIR", str(tmuxp_configdir))
    assert get_workspace_dir() == str(tmuxp_configdir)


@pytest.fixture()
def monkeypatch_plugin_test_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    """Monkeypatch tmuxp plugin fixtures to python path."""
    paths = [
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_bwb/",
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_bs/",
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_r/",
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_owc/",
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_awf/",
        "tests/fixtures/pluginsystem/plugins/tmuxp_test_plugin_fail/",
    ]
    for path in paths:
        monkeypatch.syspath_prepend(str(pathlib.Path(path).resolve()))


@pytest.fixture()
def session_params(session_params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """Terminal-friendly tmuxp session_params for dimensions."""
    session_params.update({"x": 800, "y": 600})
    return session_params


@pytest.fixture()
def socket_name(request: pytest.FixtureRequest) -> str:
    """Random socket name for tmuxp."""
    return "tmuxp_test%s" % next(namer)


@pytest.fixture(autouse=True)
def add_doctest_fixtures(
    request: pytest.FixtureRequest,
    doctest_namespace: t.Dict[str, t.Any],
    tmp_path: pathlib.Path,
) -> None:
    """Harness pytest fixtures to doctests namespace."""
    if isinstance(request._pyfuncitem, DoctestItem) and shutil.which("tmux"):
        doctest_namespace["server"] = request.getfixturevalue("server")
        session: "Session" = request.getfixturevalue("session")
        doctest_namespace["session"] = session
        doctest_namespace["window"] = session.active_window
        doctest_namespace["pane"] = session.active_pane
        doctest_namespace["test_utils"] = test_utils
        doctest_namespace["tmp_path"] = tmp_path
