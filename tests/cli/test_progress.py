"""Tests for tmuxp CLI progress indicator."""

from __future__ import annotations

import atexit
import io
import pathlib
import time
import typing as t

import libtmux
import pytest

from tmuxp.cli._colors import ColorMode
from tmuxp.cli._progress import (
    BAR_WIDTH,
    ERASE_LINE,
    HIDE_CURSOR,
    PROGRESS_PRESETS,
    SHOW_CURSOR,
    SUCCESS_TEMPLATE,
    BuildTree,
    Spinner,
    _truncate_visible,
    _visible_len,
    render_bar,
    resolve_progress_format,
)


class SpinnerEnablementFixture(t.NamedTuple):
    """Test fixture for spinner TTY/color enablement matrix."""

    test_id: str
    isatty: bool
    color_mode: ColorMode
    expected_enabled: bool


SPINNER_ENABLEMENT_FIXTURES: list[SpinnerEnablementFixture] = [
    SpinnerEnablementFixture("tty_color_always", True, ColorMode.ALWAYS, True),
    SpinnerEnablementFixture("tty_color_auto", True, ColorMode.AUTO, True),
    SpinnerEnablementFixture("tty_color_never", True, ColorMode.NEVER, True),
    SpinnerEnablementFixture("non_tty_color_always", False, ColorMode.ALWAYS, False),
    SpinnerEnablementFixture("non_tty_color_never", False, ColorMode.NEVER, False),
]


@pytest.mark.parametrize(
    list(SpinnerEnablementFixture._fields),
    SPINNER_ENABLEMENT_FIXTURES,
    ids=[f.test_id for f in SPINNER_ENABLEMENT_FIXTURES],
)
def test_spinner_enablement(
    test_id: str,
    isatty: bool,
    color_mode: ColorMode,
    expected_enabled: bool,
) -> None:
    """Spinner._enabled depends only on TTY, not on color mode."""
    stream = io.StringIO()
    stream.isatty = lambda: isatty  # type: ignore[method-assign]

    spinner = Spinner(message="Test", color_mode=color_mode, stream=stream)
    assert spinner._enabled is expected_enabled


def test_spinner_disabled_output() -> None:
    """Disabled spinner produces no output."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    with Spinner(message="Test", stream=stream) as spinner:
        spinner.update_message("Updated")

    assert stream.getvalue() == ""


def test_spinner_enabled_output() -> None:
    """Enabled spinner writes ANSI control sequences."""
    stream = io.StringIO()
    stream.isatty = lambda: True  # type: ignore[method-assign]

    with Spinner(
        message="Test", color_mode=ColorMode.ALWAYS, stream=stream, interval=0.01
    ):
        pass  # enter and exit — enough for at least one frame + cleanup

    output = stream.getvalue()
    assert HIDE_CURSOR in output
    assert SHOW_CURSOR in output
    assert ERASE_LINE in output
    assert "Test" in output


def test_spinner_atexit_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    """atexit.register called on start, unregistered on stop."""
    registered: list[t.Any] = []
    unregistered: list[t.Any] = []
    monkeypatch.setattr(atexit, "register", lambda fn, *a: registered.append(fn))
    monkeypatch.setattr(atexit, "unregister", lambda fn: unregistered.append(fn))

    stream = io.StringIO()
    stream.isatty = lambda: True  # type: ignore[method-assign]

    with Spinner(message="Test", color_mode=ColorMode.ALWAYS, stream=stream) as spinner:
        assert len(registered) == 1
        assert spinner._restore_cursor in registered

    assert len(unregistered) == 1
    assert spinner._restore_cursor in unregistered


def test_spinner_cleans_up_on_exception() -> None:
    """SHOW_CURSOR written even when body raises."""
    stream = io.StringIO()
    stream.isatty = lambda: True  # type: ignore[method-assign]

    msg = "deliberate"
    with (
        pytest.raises(ValueError),
        Spinner(message="Test", color_mode=ColorMode.ALWAYS, stream=stream),
    ):
        raise ValueError(msg)

    assert SHOW_CURSOR in stream.getvalue()


def test_spinner_update_message_thread_safe() -> None:
    """update_message() can be called from the main thread without error."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(message="Start", color_mode=ColorMode.NEVER, stream=stream)
    spinner.update_message("Updated")
    assert spinner.message == "Updated"


def test_spinner_add_output_line_accumulates() -> None:
    """add_output_line() appends stripped lines to the panel deque on TTY."""
    stream = io.StringIO()
    stream.isatty = lambda: True  # type: ignore[method-assign]

    spinner = Spinner(message="Test", color_mode=ColorMode.NEVER, stream=stream)
    spinner.add_output_line("Session created: test\n")
    spinner.add_output_line("Creating window: editor")
    spinner.add_output_line("")  # blank lines are ignored

    assert list(spinner._output_lines) == [
        "Session created: test",
        "Creating window: editor",
    ]


def test_spinner_panel_respects_maxlen() -> None:
    """Panel deque enforces output_lines maxlen, dropping oldest lines."""
    stream = io.StringIO()
    stream.isatty = lambda: True  # type: ignore[method-assign]

    spinner = Spinner(
        message="Test", color_mode=ColorMode.NEVER, stream=stream, output_lines=3
    )
    for i in range(5):
        spinner.add_output_line(f"line {i}")

    panel = list(spinner._output_lines)
    assert len(panel) == 3
    assert panel == ["line 2", "line 3", "line 4"]


def test_spinner_panel_rendered_in_output() -> None:
    """Enabled spinner writes panel lines and spinner line to stream."""
    stream = io.StringIO()
    stream.isatty = lambda: True  # type: ignore[method-assign]

    with Spinner(
        message="Building...", color_mode=ColorMode.ALWAYS, stream=stream, interval=0.01
    ) as spinner:
        spinner.add_output_line("Session created: my-session")
        # Wait long enough for the spinner thread to render at least one frame
        # that includes the panel line (interval=0.01s, so 0.05s is sufficient).
        time.sleep(0.05)

    output = stream.getvalue()
    assert HIDE_CURSOR in output
    assert SHOW_CURSOR in output
    assert "Session created: my-session" in output
    assert "Building..." in output


# BuildTree tests


def test_build_tree_empty_renders_nothing() -> None:
    """BuildTree.render() returns [] before any session_created event."""
    colors = ColorMode.NEVER
    tree = BuildTree()
    from tmuxp.cli._colors import Colors

    assert tree.render(Colors(colors), 80) == []


def test_build_tree_session_created_shows_header() -> None:
    """After session_created, render() returns the 'Session' heading line."""
    from tmuxp.cli._colors import Colors

    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "my-session"})
    lines = tree.render(Colors(ColorMode.NEVER), 80)
    assert lines == ["Session"]


def test_build_tree_window_started_no_pane_yet() -> None:
    """window_started adds a window line with just the name (no pane info)."""
    from tmuxp.cli._colors import Colors

    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "my-session"})
    tree.on_event({"event": "window_started", "name": "editor", "pane_total": 2})
    lines = tree.render(Colors(ColorMode.NEVER), 80)
    assert len(lines) == 2
    assert lines[1] == "- editor"


def test_build_tree_pane_creating_shows_progress() -> None:
    """pane_creating updates the last window to show pane N of M."""
    from tmuxp.cli._colors import Colors

    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "my-session"})
    tree.on_event({"event": "window_started", "name": "editor", "pane_total": 3})
    tree.on_event({"event": "pane_creating", "pane_num": 2, "pane_total": 3})
    lines = tree.render(Colors(ColorMode.NEVER), 80)
    assert lines[1] == "- editor, pane (2 of 3)"


def test_build_tree_window_done_shows_checkmark() -> None:
    """window_done marks the window as done; render shows checkmark."""
    from tmuxp.cli._colors import Colors

    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "my-session"})
    tree.on_event({"event": "window_started", "name": "editor", "pane_total": 1})
    tree.on_event({"event": "pane_creating", "pane_num": 1, "pane_total": 1})
    tree.on_event({"event": "window_done"})
    lines = tree.render(Colors(ColorMode.NEVER), 80)
    assert lines[1] == "- ✓ editor"


def test_build_tree_workspace_built_marks_all_done() -> None:
    """workspace_built marks all windows as done."""
    from tmuxp.cli._colors import Colors

    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "my-session"})
    tree.on_event({"event": "window_started", "name": "editor", "pane_total": 1})
    tree.on_event({"event": "window_started", "name": "logs", "pane_total": 1})
    tree.on_event({"event": "workspace_built"})
    lines = tree.render(Colors(ColorMode.NEVER), 80)
    assert lines[1] == "- ✓ editor"
    assert lines[2] == "- ✓ logs"


def test_build_tree_multiple_windows_accumulate() -> None:
    """Multiple window_started events accumulate into separate tree lines."""
    from tmuxp.cli._colors import Colors

    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "my-session"})
    tree.on_event({"event": "window_started", "name": "editor", "pane_total": 2})
    tree.on_event({"event": "window_done"})
    tree.on_event({"event": "window_started", "name": "logging", "pane_total": 1})
    tree.on_event({"event": "pane_creating", "pane_num": 1, "pane_total": 1})
    lines = tree.render(Colors(ColorMode.NEVER), 80)
    assert lines[1] == "- ✓ editor"
    assert lines[2] == "- logging, pane (1 of 1)"


def test_spinner_on_build_event_delegates_to_tree() -> None:
    """Spinner.on_build_event() updates the internal BuildTree state."""
    import io

    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(message="Building...", color_mode=ColorMode.NEVER, stream=stream)
    spinner.on_build_event({"event": "session_created", "name": "test-session"})
    spinner.on_build_event(
        {"event": "window_started", "name": "editor", "pane_total": 1}
    )

    assert spinner._build_tree.session_name == "test-session"
    assert len(spinner._build_tree.windows) == 1
    assert spinner._build_tree.windows[0].name == "editor"


# BuildTree.format_inline tests


def test_build_tree_format_inline_empty() -> None:
    """format_inline returns base unchanged when no session has been created."""
    tree = BuildTree()
    assert tree.format_inline("Building projects...") == "Building projects..."


def test_build_tree_format_inline_session_only() -> None:
    """format_inline returns 'base session' after session_created with no windows."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    assert tree.format_inline("Building projects...") == "Building projects... cihai"


def test_build_tree_format_inline_with_window_total() -> None:
    """format_inline shows window index/total bracket after window_started."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    tree.on_event({"event": "window_started", "name": "gp-libs", "pane_total": 2})
    result = tree.format_inline("Building projects...")
    assert result == "Building projects... cihai [1 of 3 windows] gp-libs"


def test_build_tree_format_inline_with_panes() -> None:
    """format_inline includes pane progress once pane_creating fires."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    tree.on_event({"event": "window_started", "name": "gp-libs", "pane_total": 2})
    tree.on_event({"event": "pane_creating", "pane_num": 1, "pane_total": 2})
    result = tree.format_inline("Building projects...")
    assert result == "Building projects... cihai [1 of 3 windows, 1 of 2 panes] gp-libs"


def test_build_tree_format_inline_no_window_total() -> None:
    """format_inline omits window count bracket when window_total is absent."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai"})
    tree.on_event({"event": "window_started", "name": "main", "pane_total": 1})
    tree.on_event({"event": "pane_creating", "pane_num": 1, "pane_total": 1})
    result = tree.format_inline("Building...")
    assert result == "Building... cihai [1 of 1 panes] main"


def test_spinner_on_build_event_updates_message() -> None:
    """on_build_event updates spinner.message via format_inline after each event."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Building...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        progress_format=None,
    )
    assert spinner.message == "Building..."

    spinner.on_build_event(
        {"event": "session_created", "name": "cihai", "window_total": 2}
    )
    assert spinner.message == "Building... cihai"

    spinner.on_build_event(
        {"event": "window_started", "name": "editor", "pane_total": 3}
    )
    assert spinner.message == "Building... cihai [1 of 2 windows] editor"

    spinner.on_build_event({"event": "pane_creating", "pane_num": 2, "pane_total": 3})
    assert spinner.message == "Building... cihai [1 of 2 windows, 2 of 3 panes] editor"


# resolve_progress_format tests


def test_resolve_progress_format_preset_name() -> None:
    """A known preset name resolves to its format string."""
    assert resolve_progress_format("default") == PROGRESS_PRESETS["default"]
    assert resolve_progress_format("minimal") == PROGRESS_PRESETS["minimal"]
    assert resolve_progress_format("verbose") == PROGRESS_PRESETS["verbose"]


def test_resolve_progress_format_raw_string() -> None:
    """A raw template string is returned unchanged."""
    raw = "{session} w{window_progress}"
    assert resolve_progress_format(raw) == raw


def test_resolve_progress_format_unknown_name() -> None:
    """An unknown name not in presets is returned as-is (raw template pass-through)."""
    assert resolve_progress_format("not-a-preset") == "not-a-preset"


# BuildTree.format_template tests


def test_build_tree_format_template_before_session() -> None:
    """format_template returns '' before session_created fires."""
    tree = BuildTree()
    assert tree.format_template("{session} [{progress}] {window}") == ""


def test_build_tree_format_template_session_only() -> None:
    """After session_created alone, progress and window are empty."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    assert tree.format_template("{session} [{progress}] {window}") == "cihai [] "


def test_build_tree_format_template_with_window() -> None:
    """After window_started, window progress appears but pane progress does not."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    tree.on_event({"event": "window_started", "name": "editor", "pane_total": 4})
    assert (
        tree.format_template("{session} [{progress}] {window}")
        == "cihai [1/3 win] editor"
    )


def test_build_tree_format_template_with_pane() -> None:
    """After pane_creating, both window and pane progress appear."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    tree.on_event({"event": "window_started", "name": "editor", "pane_total": 4})
    tree.on_event({"event": "pane_creating", "pane_num": 2, "pane_total": 4})
    assert (
        tree.format_template("{session} [{progress}] {window}")
        == "cihai [1/3 win · 2/4 pane] editor"
    )


def test_build_tree_format_template_minimal() -> None:
    """The minimal preset-style template shows only window fraction."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    tree.on_event({"event": "window_started", "name": "editor", "pane_total": 4})
    assert tree.format_template("{session} [{window_progress}]") == "cihai [1/3]"


def test_build_tree_format_template_verbose() -> None:
    """Verbose template shows window/pane indices and totals explicitly."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 12})
    tree.on_event({"event": "window_started", "name": "editor", "pane_total": 4})
    tree.on_event({"event": "pane_creating", "pane_num": 2, "pane_total": 4})
    result = tree.format_template(PROGRESS_PRESETS["verbose"])
    assert result == "Loading workspace: cihai [window 1 of 12 · pane 2 of 4] editor"


def test_build_tree_format_template_bad_token() -> None:
    """Unknown tokens are left as {name}, known tokens still resolve."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    result = tree.format_template("{session} {unknown}")
    # _SafeFormatMap: {session} resolves, {unknown} stays as-is
    assert result == "cihai {unknown}"


# Spinner.progress_format integration tests


def test_spinner_progress_format_updates_message() -> None:
    """Spinner with explicit progress_format uses format_template for updates."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    # Use an explicit format string rather than "default" preset to avoid
    # coupling this test to the preset definition (which now includes {bar}).
    spinner = Spinner(
        message="Building...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        progress_format="{session} [{progress}] {window}",
    )
    assert spinner.message == "Building..."

    spinner.on_build_event(
        {"event": "session_created", "name": "cihai", "window_total": 3}
    )
    # No windows yet — falls back to base message to avoid showing empty brackets.
    assert spinner.message == "Building..."

    spinner.on_build_event(
        {"event": "window_started", "name": "editor", "pane_total": 4}
    )
    assert spinner.message == "cihai [1/3 win] editor"

    spinner.on_build_event({"event": "pane_creating", "pane_num": 2, "pane_total": 4})
    assert spinner.message == "cihai [1/3 win · 2/4 pane] editor"


def test_spinner_progress_format_none_uses_inline() -> None:
    """Spinner with progress_format=None preserves the format_inline path."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Building...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        progress_format=None,
    )

    spinner.on_build_event(
        {"event": "session_created", "name": "cihai", "window_total": 2}
    )
    assert spinner.message == "Building... cihai"

    spinner.on_build_event(
        {"event": "window_started", "name": "editor", "pane_total": 3}
    )
    assert spinner.message == "Building... cihai [1 of 2 windows] editor"


# render_bar tests


def test_render_bar_empty() -> None:
    """render_bar with done=0 produces an all-empty bar."""
    assert render_bar(0, 10) == "░░░░░░░░░░"


def test_render_bar_half() -> None:
    """render_bar with done=5, total=10 fills exactly half."""
    assert render_bar(5, 10) == "█████░░░░░"


def test_render_bar_full() -> None:
    """render_bar with done=total fills the entire bar."""
    assert render_bar(10, 10) == "██████████"


def test_render_bar_zero_total() -> None:
    """render_bar with total=0 returns empty string."""
    assert render_bar(0, 0) == ""


def test_render_bar_custom_width() -> None:
    """render_bar with custom width produces bar of that inner width."""
    assert render_bar(3, 10, width=5) == "█░░░░"


def test_render_bar_width_constant() -> None:
    """BAR_WIDTH is the default inner width used by render_bar."""
    bar = render_bar(0, 10)
    assert len(bar) == BAR_WIDTH


# BuildTree new token tests


def test_build_tree_context_session_pane_total() -> None:
    """session_pane_total token reflects count from session_created event."""
    tree = BuildTree()
    tree.on_event(
        {
            "event": "session_created",
            "name": "s",
            "window_total": 2,
            "session_pane_total": 8,
        }
    )
    ctx = tree._context()
    assert ctx["session_pane_total"] == 8
    assert ctx["session_pane_progress"] == "0/8"
    assert ctx["overall_percent"] == 0


def test_build_tree_context_window_progress_rel() -> None:
    """window_progress_rel is 0/N from session_created, increments on window_done."""
    tree = BuildTree()
    tree.on_event(
        {
            "event": "session_created",
            "name": "s",
            "window_total": 3,
            "session_pane_total": 6,
        }
    )
    assert tree._context()["window_progress_rel"] == "0/3"

    tree.on_event({"event": "window_started", "name": "w1", "pane_total": 2})
    assert tree._context()["window_progress_rel"] == "0/3"

    tree.on_event({"event": "window_done"})
    assert tree._context()["window_progress_rel"] == "1/3"


def test_build_tree_context_pane_progress_rel() -> None:
    """pane_progress_rel shows 0/M after window_started, N/M after pane_creating."""
    tree = BuildTree()
    tree.on_event(
        {
            "event": "session_created",
            "name": "s",
            "window_total": 1,
            "session_pane_total": 4,
        }
    )
    tree.on_event({"event": "window_started", "name": "w1", "pane_total": 4})
    assert tree._context()["pane_progress_rel"] == "0/4"

    tree.on_event({"event": "pane_creating", "pane_num": 2, "pane_total": 4})
    assert tree._context()["pane_progress_rel"] == "2/4"
    assert tree._context()["pane_done"] == 2
    assert tree._context()["pane_remaining"] == 2


def test_build_tree_context_overall_percent() -> None:
    """overall_percent is pane-based 0-100; updates on window_done."""
    tree = BuildTree()
    tree.on_event(
        {
            "event": "session_created",
            "name": "s",
            "window_total": 2,
            "session_pane_total": 8,
        }
    )
    assert tree._context()["overall_percent"] == 0

    tree.on_event({"event": "window_started", "name": "w1", "pane_total": 4})
    tree.on_event({"event": "window_done"})
    assert tree._context()["session_panes_done"] == 4
    assert tree._context()["overall_percent"] == 50


def test_build_tree_before_script_event_toggle() -> None:
    """before_script_started sets the Event; before_script_done clears it."""
    tree = BuildTree()
    assert not tree._before_script_event.is_set()

    tree.on_event({"event": "before_script_started"})
    assert tree._before_script_event.is_set()

    tree.on_event({"event": "before_script_done"})
    assert not tree._before_script_event.is_set()


def test_build_tree_zero_pane_window() -> None:
    """Windows with pane_total=0 do not cause division-by-zero or exceptions."""
    tree = BuildTree()
    tree.on_event(
        {
            "event": "session_created",
            "name": "s",
            "window_total": 1,
            "session_pane_total": 0,
        }
    )
    tree.on_event({"event": "window_started", "name": "w1", "pane_total": 0})
    tree.on_event({"event": "window_done"})

    assert tree.session_panes_done == 0
    assert tree.windows_done == 1
    ctx = tree._context()
    assert ctx["session_pane_progress"] == ""
    assert ctx["overall_percent"] == 0


def test_format_template_extra_backward_compat() -> None:
    """format_template(fmt) without extra still works as before."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    result = tree.format_template("{session} [{progress}] {window}")
    assert result == "cihai [] "


def test_format_template_extra_injected() -> None:
    """format_template resolves extra tokens from the extra dict."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    result = tree.format_template("{session} {bar}", extra={"bar": "[TEST_BAR]"})
    assert result == "cihai [TEST_BAR]"


def test_format_template_unknown_token_preserved() -> None:
    """Unknown tokens in the format string render as {name}, not blank or raw fmt."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "cihai", "window_total": 3})
    result = tree.format_template("{session} {unknown_token}")
    assert result == "cihai {unknown_token}"


# Spinner bar token tests


def test_spinner_bar_token_no_color() -> None:
    """With ColorMode.NEVER, {bar} token in message contains bar characters."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Building...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        progress_format="{session} {bar} {progress} {window}",
    )
    spinner.on_build_event(
        {
            "event": "session_created",
            "name": "cihai",
            "window_total": 3,
            "session_pane_total": 6,
        }
    )
    spinner.on_build_event(
        {"event": "window_started", "name": "editor", "pane_total": 2}
    )
    spinner.on_build_event({"event": "pane_creating", "pane_num": 1, "pane_total": 2})

    assert "░" in spinner.message or "█" in spinner.message


def test_spinner_pane_bar_preset() -> None:
    """The 'pane' preset wires {pane_bar} and {session_pane_progress}."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Building...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        progress_format="pane",
    )
    spinner.on_build_event(
        {
            "event": "session_created",
            "name": "s",
            "window_total": 2,
            "session_pane_total": 4,
        }
    )
    spinner.on_build_event({"event": "window_started", "name": "w1", "pane_total": 2})
    spinner.on_build_event({"event": "window_done"})

    assert "2/4" in spinner.message
    assert "░" in spinner.message or "█" in spinner.message


def test_spinner_before_script_event_via_events() -> None:
    """before_script_started / before_script_done toggle the BuildTree Event flag."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Building...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        progress_format="default",
    )
    spinner.on_build_event({"event": "before_script_started"})
    assert spinner._build_tree._before_script_event.is_set()

    spinner.on_build_event({"event": "before_script_done"})
    assert not spinner._build_tree._before_script_event.is_set()


def test_progress_presets_have_expected_keys() -> None:
    """All expected preset names are present in PROGRESS_PRESETS."""
    for name in ("default", "minimal", "window", "pane", "verbose"):
        assert name in PROGRESS_PRESETS, f"Missing preset: {name}"


def test_progress_presets_default_includes_bar() -> None:
    """The 'default' preset includes the {bar} token."""
    assert "{bar}" in PROGRESS_PRESETS["default"]


def test_progress_presets_minimal_format() -> None:
    """The 'minimal' preset includes the Loading prefix and window_progress token."""
    expected = "Loading workspace: {session} [{window_progress}]"
    assert PROGRESS_PRESETS["minimal"] == expected


# BuildTree remaining token tests


class RemainingTokenFixture(t.NamedTuple):
    """Test fixture for windows_remaining and session_panes_remaining tokens."""

    test_id: str
    events: list[dict[str, t.Any]]
    token: str
    expected: int


REMAINING_TOKEN_FIXTURES: list[RemainingTokenFixture] = [
    RemainingTokenFixture(
        "windows_remaining_initial",
        [
            {
                "event": "session_created",
                "name": "s",
                "window_total": 3,
                "session_pane_total": 6,
            },
        ],
        "windows_remaining",
        3,
    ),
    RemainingTokenFixture(
        "windows_remaining_after_done",
        [
            {
                "event": "session_created",
                "name": "s",
                "window_total": 3,
                "session_pane_total": 6,
            },
            {"event": "window_started", "name": "w1", "pane_total": 2},
            {"event": "window_done"},
        ],
        "windows_remaining",
        2,
    ),
    RemainingTokenFixture(
        "session_panes_remaining_initial",
        [
            {
                "event": "session_created",
                "name": "s",
                "window_total": 2,
                "session_pane_total": 5,
            },
        ],
        "session_panes_remaining",
        5,
    ),
    RemainingTokenFixture(
        "session_panes_remaining_after_window",
        [
            {
                "event": "session_created",
                "name": "s",
                "window_total": 2,
                "session_pane_total": 5,
            },
            {"event": "window_started", "name": "w1", "pane_total": 3},
            {"event": "window_done"},
        ],
        "session_panes_remaining",
        2,
    ),
]


@pytest.mark.parametrize(
    list(RemainingTokenFixture._fields),
    REMAINING_TOKEN_FIXTURES,
    ids=[f.test_id for f in REMAINING_TOKEN_FIXTURES],
)
def test_build_tree_remaining_tokens(
    test_id: str,
    events: list[dict[str, t.Any]],
    token: str,
    expected: int,
) -> None:
    """Remaining tokens decrement correctly as windows/panes complete."""
    tree = BuildTree()
    for ev in events:
        tree.on_event(ev)
    assert tree._context()[token] == expected


# _visible_len tests


class VisibleLenFixture(t.NamedTuple):
    """Test fixture for _visible_len ANSI-aware length calculation."""

    test_id: str
    text: str
    expected_len: int


VISIBLE_LEN_FIXTURES: list[VisibleLenFixture] = [
    VisibleLenFixture("plain_text", "hello", 5),
    VisibleLenFixture("ansi_green", "\033[32mgreen\033[0m", 5),
    VisibleLenFixture("empty_string", "", 0),
    VisibleLenFixture("nested_ansi", "\033[1m\033[31mbold red\033[0m", 8),
    VisibleLenFixture("ansi_only", "\033[0m", 0),
]


@pytest.mark.parametrize(
    list(VisibleLenFixture._fields),
    VISIBLE_LEN_FIXTURES,
    ids=[f.test_id for f in VISIBLE_LEN_FIXTURES],
)
def test_visible_len(
    test_id: str,
    text: str,
    expected_len: int,
) -> None:
    """_visible_len returns the visible character count, ignoring ANSI escapes."""
    assert _visible_len(text) == expected_len


# Spinner.add_output_line non-TTY write-through tests


class OutputLineFixture(t.NamedTuple):
    """Test fixture for add_output_line TTY vs non-TTY behavior."""

    test_id: str
    isatty: bool
    lines: list[str]
    expected_deque: list[str]
    expected_stream_contains: str


OUTPUT_LINE_FIXTURES: list[OutputLineFixture] = [
    OutputLineFixture(
        "tty_accumulates_in_deque",
        isatty=True,
        lines=["line1\n", "line2\n"],
        expected_deque=["line1", "line2"],
        expected_stream_contains="",
    ),
    OutputLineFixture(
        "non_tty_writes_to_stream",
        isatty=False,
        lines=["hello\n", "world\n"],
        expected_deque=[],
        expected_stream_contains="hello\nworld\n",
    ),
    OutputLineFixture(
        "blank_lines_ignored",
        isatty=True,
        lines=["", "\n"],
        expected_deque=[],
        expected_stream_contains="",
    ),
]


@pytest.mark.parametrize(
    list(OutputLineFixture._fields),
    OUTPUT_LINE_FIXTURES,
    ids=[f.test_id for f in OUTPUT_LINE_FIXTURES],
)
def test_spinner_output_line_behavior(
    test_id: str,
    isatty: bool,
    lines: list[str],
    expected_deque: list[str],
    expected_stream_contains: str,
) -> None:
    """add_output_line accumulates in deque (TTY) or writes to stream (non-TTY)."""
    stream = io.StringIO()
    stream.isatty = lambda: isatty  # type: ignore[method-assign]

    spinner = Spinner(message="Test", color_mode=ColorMode.NEVER, stream=stream)
    for line in lines:
        spinner.add_output_line(line)

    assert list(spinner._output_lines) == expected_deque
    assert expected_stream_contains in stream.getvalue()


# Spinner.success tests


# Panel lines special values tests


class PanelLinesFixture(t.NamedTuple):
    """Test fixture for Spinner panel_lines special values."""

    test_id: str
    output_lines: int
    expected_maxlen: int | None  # None = unbounded
    expected_hidden: bool
    add_count: int
    expected_retained: int


PANEL_LINES_FIXTURES: list[PanelLinesFixture] = [
    PanelLinesFixture("zero_hides_panel", 0, 1, True, 10, 1),
    PanelLinesFixture("negative_unlimited", -1, None, False, 100, 100),
    PanelLinesFixture("positive_normal", 5, 5, False, 10, 5),
    PanelLinesFixture("default_three", 3, 3, False, 5, 3),
]


@pytest.mark.parametrize(
    list(PanelLinesFixture._fields),
    PANEL_LINES_FIXTURES,
    ids=[f.test_id for f in PANEL_LINES_FIXTURES],
)
def test_spinner_panel_lines_special_values(
    test_id: str,
    output_lines: int,
    expected_maxlen: int | None,
    expected_hidden: bool,
    add_count: int,
    expected_retained: int,
) -> None:
    """Spinner panel_lines=0 hides, -1 is unlimited, positive caps normally."""
    stream = io.StringIO()
    stream.isatty = lambda: True  # type: ignore[method-assign]

    spinner = Spinner(
        message="Test",
        color_mode=ColorMode.NEVER,
        stream=stream,
        output_lines=output_lines,
    )
    for i in range(add_count):
        spinner.add_output_line(f"line {i}")

    assert len(spinner._output_lines) == expected_retained
    assert spinner._output_lines.maxlen == expected_maxlen
    assert spinner._panel_hidden is expected_hidden


def test_spinner_unlimited_caps_rendered_panel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unlimited panel (-1) caps rendered lines to terminal_height - 2."""
    import os as _os
    import shutil

    monkeypatch.setattr(
        shutil,
        "get_terminal_size",
        lambda fallback=(80, 24): _os.terminal_size((80, 10)),
    )

    stream = io.StringIO()
    stream.isatty = lambda: True  # type: ignore[method-assign]

    spinner = Spinner(
        message="Test",
        color_mode=ColorMode.NEVER,
        stream=stream,
        output_lines=-1,
        interval=0.01,
    )
    for i in range(50):
        spinner.add_output_line(f"line {i}")

    # All 50 lines should be retained in the unbounded deque
    assert len(spinner._output_lines) == 50

    # Start spinner briefly to render at least one frame
    spinner.start()
    time.sleep(0.05)
    spinner.stop()

    output = stream.getvalue()
    # Verify that not all 50 lines appear in any single frame
    # The cap should limit to terminal_height - 2 = 8 lines
    # Only the last 8 lines should appear in output
    assert "line 49" in output
    assert "line 0" not in output


class SuccessFixture(t.NamedTuple):
    """Test fixture for Spinner.success() output behavior."""

    test_id: str
    isatty: bool
    color_mode: ColorMode
    expected_contains: str


SUCCESS_FIXTURES: list[SuccessFixture] = [
    SuccessFixture("tty_with_color", True, ColorMode.ALWAYS, "done"),
    SuccessFixture("tty_no_color", True, ColorMode.NEVER, "✓ done"),
    SuccessFixture("non_tty", False, ColorMode.NEVER, "✓ done"),
]


@pytest.mark.parametrize(
    list(SuccessFixture._fields),
    SUCCESS_FIXTURES,
    ids=[f.test_id for f in SUCCESS_FIXTURES],
)
def test_spinner_success_behavior(
    test_id: str,
    isatty: bool,
    color_mode: ColorMode,
    expected_contains: str,
) -> None:
    """success() always emits the checkmark message regardless of TTY/color mode."""
    stream = io.StringIO()
    stream.isatty = lambda: isatty  # type: ignore[method-assign]

    spinner = Spinner(message="Test", color_mode=color_mode, stream=stream)
    spinner.success("done")

    output = stream.getvalue()
    assert "✓" in output
    assert expected_contains in output


# _truncate_visible tests


def test_truncate_visible_plain_text() -> None:
    """Plain text is truncated to max_visible chars with default suffix."""
    assert _truncate_visible("hello world", 5) == "hello\x1b[0m..."


def test_truncate_visible_ansi_preserved() -> None:
    """ANSI sequences are preserved whole; only visible chars count."""
    result = _truncate_visible("\033[32mgreen\033[0m", 3)
    assert result == "\x1b[32mgre\x1b[0m..."


def test_truncate_visible_no_truncation() -> None:
    """String shorter than max_visible is returned unchanged."""
    assert _truncate_visible("short", 10) == "short"


def test_truncate_visible_empty() -> None:
    """Empty string returns empty string."""
    assert _truncate_visible("", 5) == ""


def test_truncate_visible_custom_suffix() -> None:
    """Custom suffix is appended after truncation."""
    assert _truncate_visible("hello world", 5, suffix="~") == "hello\x1b[0m~"


def test_truncate_visible_no_suffix() -> None:
    """Empty suffix produces only the reset sequence."""
    assert _truncate_visible("hello world", 5, suffix="") == "hello\x1b[0m"


# workspace_path token tests


def test_build_tree_workspace_path_in_context() -> None:
    """workspace_path is available in _context() when set on construction."""
    tree = BuildTree(workspace_path="~/.tmuxp/foo.yaml")
    tree.on_event({"event": "session_created", "name": "foo", "window_total": 1})
    ctx = tree._context()
    assert ctx["workspace_path"] == "~/.tmuxp/foo.yaml"


def test_build_tree_workspace_path_empty_default() -> None:
    """workspace_path defaults to empty string in _context()."""
    tree = BuildTree()
    tree.on_event({"event": "session_created", "name": "s", "window_total": 1})
    assert tree._context()["workspace_path"] == ""


def test_spinner_workspace_path_passed_to_tree() -> None:
    """Spinner passes workspace_path through to its BuildTree."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Loading...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        workspace_path="~/.tmuxp/proj.yaml",
    )
    assert spinner._build_tree.workspace_path == "~/.tmuxp/proj.yaml"


def test_build_tree_workspace_path_in_template() -> None:
    """workspace_path token resolves in format_template."""
    tree = BuildTree(workspace_path="~/.tmuxp/bar.yaml")
    tree.on_event({"event": "session_created", "name": "bar", "window_total": 1})
    result = tree.format_template("{session} ({workspace_path})")
    assert result == "bar (~/.tmuxp/bar.yaml)"


# {summary} token tests


def test_build_tree_summary_empty_state() -> None:
    """Summary token is empty string before any windows complete."""
    tree = BuildTree()
    tree.on_event(
        {
            "event": "session_created",
            "name": "s",
            "window_total": 3,
            "session_pane_total": 6,
        }
    )
    assert tree._context()["summary"] == ""


def test_build_tree_summary_after_windows_done() -> None:
    """Summary token shows bracketed win/pane counts after windows complete."""
    tree = BuildTree()
    tree.on_event(
        {
            "event": "session_created",
            "name": "s",
            "window_total": 3,
            "session_pane_total": 8,
        }
    )
    tree.on_event({"event": "window_started", "name": "w1", "pane_total": 3})
    tree.on_event({"event": "window_done"})
    tree.on_event({"event": "window_started", "name": "w2", "pane_total": 2})
    tree.on_event({"event": "window_done"})
    tree.on_event({"event": "window_started", "name": "w3", "pane_total": 3})
    tree.on_event({"event": "window_done"})
    assert tree._context()["summary"] == "[3 win, 8 panes]"


def test_build_tree_summary_windows_only_no_panes() -> None:
    """Summary token shows only win count when pane_total is 0."""
    tree = BuildTree()
    tree.on_event(
        {
            "event": "session_created",
            "name": "s",
            "window_total": 2,
            "session_pane_total": 0,
        }
    )
    tree.on_event({"event": "window_started", "name": "w1", "pane_total": 0})
    tree.on_event({"event": "window_done"})
    tree.on_event({"event": "window_started", "name": "w2", "pane_total": 0})
    tree.on_event({"event": "window_done"})
    assert tree._context()["summary"] == "[2 win]"


def test_build_tree_summary_panes_only() -> None:
    """Summary token shows only pane count when windows_done is 0 (edge case)."""
    tree = BuildTree()
    tree.on_event(
        {
            "event": "session_created",
            "name": "s",
            "window_total": 1,
            "session_pane_total": 6,
        }
    )
    # Manually set session_panes_done without window_done to test edge case
    tree.session_panes_done = 6
    assert tree._context()["summary"] == "[6 panes]"


# format_success() tests


def test_spinner_format_success_full_build() -> None:
    """format_success renders SUCCESS_TEMPLATE with session, path, and summary."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Loading...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        workspace_path="~/.tmuxp/myapp.yaml",
    )
    spinner._build_tree.on_event(
        {
            "event": "session_created",
            "name": "myapp",
            "window_total": 3,
            "session_pane_total": 8,
        }
    )
    spinner._build_tree.on_event(
        {"event": "window_started", "name": "w1", "pane_total": 3}
    )
    spinner._build_tree.on_event({"event": "window_done"})
    spinner._build_tree.on_event(
        {"event": "window_started", "name": "w2", "pane_total": 2}
    )
    spinner._build_tree.on_event({"event": "window_done"})
    spinner._build_tree.on_event(
        {"event": "window_started", "name": "w3", "pane_total": 3}
    )
    spinner._build_tree.on_event({"event": "window_done"})

    result = spinner.format_success()
    assert "Loaded workspace:" in result
    assert "myapp" in result
    assert "~/.tmuxp/myapp.yaml" in result
    assert "[3 win, 8 panes]" in result


def test_spinner_format_success_no_windows() -> None:
    """format_success with no windows/panes done omits brackets."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Loading...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        workspace_path="~/.tmuxp/empty.yaml",
    )
    spinner._build_tree.on_event(
        {
            "event": "session_created",
            "name": "empty",
            "window_total": 0,
            "session_pane_total": 0,
        }
    )

    result = spinner.format_success()
    assert "Loaded workspace:" in result
    assert "empty" in result
    assert "~/.tmuxp/empty.yaml" in result
    assert "[" not in result


# Spinner.success() with no args tests


def test_spinner_success_no_args_template_mode() -> None:
    """success() with no args uses format_success when progress_format is set."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Loading...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        progress_format="default",
        workspace_path="~/.tmuxp/proj.yaml",
    )
    spinner._build_tree.on_event(
        {
            "event": "session_created",
            "name": "proj",
            "window_total": 1,
            "session_pane_total": 2,
        }
    )
    spinner._build_tree.on_event(
        {"event": "window_started", "name": "main", "pane_total": 2}
    )
    spinner._build_tree.on_event({"event": "window_done"})

    spinner.success()

    output = stream.getvalue()
    assert "✓" in output
    assert "Loaded workspace:" in output
    assert "proj" in output
    assert "~/.tmuxp/proj.yaml" in output
    assert "[1 win, 2 panes]" in output


def test_spinner_success_no_args_no_template() -> None:
    """success() with no args and no progress_format falls back to _base_message."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Loading workspace: myapp",
        color_mode=ColorMode.NEVER,
        stream=stream,
        progress_format=None,
    )
    spinner.success()

    output = stream.getvalue()
    assert "✓ Loading workspace: myapp" in output


def test_spinner_success_explicit_text_backward_compat() -> None:
    """success('custom text') still works as before (backward compat)."""
    stream = io.StringIO()
    stream.isatty = lambda: False  # type: ignore[method-assign]

    spinner = Spinner(
        message="Loading...",
        color_mode=ColorMode.NEVER,
        stream=stream,
        progress_format="default",
    )
    spinner.success("custom done message")

    output = stream.getvalue()
    assert "✓ custom done message" in output


# SUCCESS_TEMPLATE constant tests


def test_success_template_value() -> None:
    """SUCCESS_TEMPLATE contains expected tokens."""
    assert "{session}" in SUCCESS_TEMPLATE
    assert "{workspace_path}" in SUCCESS_TEMPLATE
    assert "{summary}" in SUCCESS_TEMPLATE
    assert "Loaded workspace:" in SUCCESS_TEMPLATE


def test_no_success_message_on_build_error(
    server: libtmux.Server,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """Success message is not emitted when _dispatch_build returns None."""
    import yaml

    from tmuxp.cli._colors import Colors
    from tmuxp.cli.load import load_workspace

    monkeypatch.delenv("TMUX", raising=False)

    config = {"session_name": "test-fail", "windows": [{"window_name": "main"}]}
    config_file = tmp_path / "fail.yaml"
    config_file.write_text(yaml.dump(config))

    monkeypatch.setattr(
        "tmuxp.cli.load._dispatch_build",
        lambda *args, **kwargs: None,
    )

    result = load_workspace(
        str(config_file),
        socket_name=server.socket_name,
        cli_colors=Colors(ColorMode.NEVER),
    )

    assert result is None
    captured = capfd.readouterr()
    assert "\u2713" not in captured.err
    assert "Loaded workspace:" not in captured.err
