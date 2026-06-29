"""Tests for :meth:`ClassicWorkspaceBuilder._bulk_set_options`."""

from __future__ import annotations

import typing as t

import libtmux
import pytest

from tmuxp.workspace.builder.classic import ClassicWorkspaceBuilder

if t.TYPE_CHECKING:
    from libtmux.session import Session


def _build(session: Session) -> ClassicWorkspaceBuilder:
    """Build a single-window session and return its builder."""
    session_config = {
        "session_name": "bulk-set-options",
        "windows": [{"window_name": "main", "panes": [{"shell_command": []}]}],
    }
    builder = ClassicWorkspaceBuilder(
        session_config=session_config,
        server=session.server,
    )
    builder.build(session=session)
    return builder


class BulkSetCase(t.NamedTuple):
    """Case for :meth:`ClassicWorkspaceBuilder._bulk_set_options` scopes."""

    test_id: str
    scope_flag: str
    option: str
    raw_value: int | str | bool
    expected: int | str | bool


BULK_SET_CASES: list[BulkSetCase] = [
    BulkSetCase(
        test_id="session-string",
        scope_flag="-s",
        option="default-shell",
        raw_value="/bin/sh",
        expected="/bin/sh",
    ),
    BulkSetCase(
        test_id="global-int",
        scope_flag="-g",
        option="repeat-time",
        raw_value=491,
        expected=491,
    ),
    BulkSetCase(
        test_id="global-bool-true",
        scope_flag="-g",
        option="visual-silence",
        raw_value=True,
        expected=True,
    ),
    BulkSetCase(
        test_id="window-bool-true",
        scope_flag="-w",
        option="automatic-rename",
        raw_value=True,
        expected=True,
    ),
    BulkSetCase(
        test_id="window-bool-false",
        scope_flag="-w",
        option="automatic-rename",
        raw_value=False,
        expected=False,
    ),
    BulkSetCase(
        test_id="window-int",
        scope_flag="-w",
        option="main-pane-height",
        raw_value=7,
        expected=7,
    ),
    BulkSetCase(
        test_id="window-string",
        scope_flag="-w",
        option="pane-border-format",
        raw_value=" #P ",
        expected=" #P ",
    ),
]


@pytest.mark.parametrize(
    "case",
    BULK_SET_CASES,
    ids=[c.test_id for c in BULK_SET_CASES],
)
def test_bulk_set_options_applies_and_normalizes(
    session: Session,
    case: BulkSetCase,
) -> None:
    """Helper sets each scope and normalizes True/False to on/off.

    A ``bool`` raw value lands as the on/off-derived bool tmux reports back,
    proving the helper mirrors ``set_option``'s normalization.
    """
    builder = _build(session)
    sess = builder.session
    window = sess.active_window

    if case.scope_flag == "-w":
        target: str | None = window.window_id
    elif case.scope_flag == "-g":
        target = None
    else:
        target = sess.session_id

    builder._bulk_set_options(
        {case.option: case.raw_value},
        target=target,
        scope_flag=case.scope_flag,
    )

    if case.scope_flag == "-w":
        assert window.show_option(case.option) == case.expected
    elif case.scope_flag == "-g":
        assert sess.show_option(case.option, global_=True) == case.expected
    else:
        assert sess.show_option(case.option) == case.expected


def test_bulk_set_options_empty_is_noop(session: Session) -> None:
    """An empty mapping returns before issuing any tmux command.

    A bogus ``scope_flag`` would make tmux error if a command were dispatched,
    so a clean return proves the empty-mapping guard short-circuits first.
    """
    builder = _build(session)
    builder._bulk_set_options({}, target=None, scope_flag="not-a-flag")


def test_bulk_set_options_propagates_unknown_option_error(
    session: Session,
) -> None:
    """A bad option surfaces as :exc:`libtmux.exc.OptionError`."""
    builder = _build(session)
    with pytest.raises(libtmux.exc.OptionError):
        builder._bulk_set_options(
            {"this-option-does-not-exist": "value"},
            target=builder.session.session_id,
            scope_flag="-s",
        )
