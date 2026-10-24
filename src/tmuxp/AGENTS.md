# src/tmuxp/AGENTS.md

Conventions scoped to this package: logging, and the CLI's color semantics.
Everything else — prose policy, the gates, tests — is in the root
[AGENTS.md](../../AGENTS.md) and the files it points to.

## Logging

These rules guide logging changes; existing code may not yet conform to all
of them.

**Setup.** `logging.getLogger(__name__)` in every module. Add a
`NullHandler` in library `__init__.py` files. Never configure handlers,
levels, or formatters in library code — that is the application's job.

**Structured context via `extra`.** Pass structured data on every log call
where useful for filtering, searching, or test assertions.

Core keys (stable, scalar, safe at any log level):

| Key                  | Type         | Context                            |
| --------------------- | ------------- | ------------------------------------ |
| `tmux_cmd`            | `str`         | tmux command line                   |
| `tmux_subcommand`     | `str`         | tmux subcommand (e.g. `new-session`) |
| `tmux_target`         | `str`         | tmux target specifier (`mysession:1.2`) |
| `tmux_exit_code`      | `int`         | tmux process exit code              |
| `tmux_session`        | `str`         | session name                        |
| `tmux_window`         | `str`         | window name or index                |
| `tmux_pane`           | `str`         | pane identifier                     |
| `tmux_config_path`    | `str`         | workspace file path                 |
| `tmux_layout`         | `str`         | window layout string                |
| `tmux_hook_cmd`       | `str`         | lifecycle hook shell command line   |

Heavy/optional keys (DEBUG only, potentially large): `tmux_stdout`,
`tmux_stderr` (`list[str]`; truncate or cap — `%(tmux_stdout)s` produces a
`repr`).

Treat established keys as compatibility-sensitive — downstream users may
build dashboards and alerts on them. Change deliberately. Keys are
`snake_case`, not dotted, with a `tmux_` prefix; prefer stable scalars over
ad-hoc objects.

**Lazy formatting.** `logger.debug("msg %s", val)`, not an f-string: the
interpolation is skipped entirely when the level is filtered, and a log
aggregator groups `"Running %s"` as one signature instead of one per distinct
value. Guard an expensive `val` with `if logger.isEnabledFor(logging.DEBUG)`.

**`stacklevel` for wrappers.** Increment it for each wrapper layer so
`%(filename)s:%(lineno)d` and the OpenTelemetry `code.filepath` attribute
point at the real caller. Verify whenever call depth changes.

**`LoggerAdapter` for persistent context.** For objects with stable identity
(`Session`, `Window`, `Pane`), use `LoggerAdapter` instead of repeating the
same `extra` on every call. Override `process()` to merge extras; on Python
3.13+, `merge_extra=True` does this for you.

**Log levels.**

| Level     | Use for                                            |
| ---------- | ---------------------------------------------------- |
| `DEBUG`    | Internal mechanics: tmux I/O, config expansion        |
| `INFO`     | Session lifecycle: session created, window added      |
| `WARNING`  | Recoverable, user-actionable: deprecated key, missing optional program |
| `ERROR`    | Failures that stop an operation: tmux command failed, validation error |

Config-discovery noise belongs in `DEBUG`; only a surprising or
user-actionable config issue is `WARNING`.

**Message style.** Lowercase, past tense for events (`"session created"`,
`"tmux command failed"`), no trailing punctuation, details in `extra` rather
than the message string.

**Exception logging.** `logger.exception()` only inside an `except` block you
are not re-raising from. `logger.error(..., exc_info=True)` for a traceback
outside an `except` block. Avoid `logger.exception()` followed by `raise` —
it duplicates the traceback; either add `extra` context or let the exception
propagate.

**Output channels.** Two channels serve different audiences and are never
mixed:

1. Diagnostics — `logger.*()` with `extra` — for log files, `caplog`, and
   aggregators. Never styled.
2. User-facing output — what the human sees, styled via `Colors`. Commands
   with `--json`/`--ndjson` output modes use `OutputFormatter.emit_text()`
   from `tmuxp.cli._output` (silenced in machine modes); human-only commands
   use `tmuxp_echo()` from `tmuxp.log` (re-exported via `tmuxp.cli.utils`).

Raw `print()` is forbidden in command and business logic. The one place it is
allowed is the presenter layer — `_output.py` and `tmuxp_echo` themselves.

**Avoid:** f-strings/`.format()` in log calls; unguarded logging in hot
loops; catch-log-reraise without adding context; `print()` for debugging;
logging a secret env var's value (log the key name only); non-scalar ad-hoc
objects in `extra`; custom `extra` fields referenced in a format string
without a safe default (a missing key raises `KeyError`).

## CLI color semantics

The `Colors` class (`src/tmuxp/_internal/colors.py`) chooses color by
**hierarchy level** and **semantic meaning**, not by data type — inspired by
`jq` (object keys vs. values), `ripgrep` (path/line/match), and `mise`/`just`
(semantic method names).

| Level | Element type         | Method        | Color              |
| ------ | ---------------------- | -------------- | -------------------- |
| L0     | Section headers        | `heading()`    | Bright cyan + bold  |
| L1     | Primary content        | `highlight()`  | Magenta + bold      |
| L2     | Supplementary info     | `info()`       | Cyan                |
| L3     | Metadata/labels        | `muted()`      | Blue                |

Status colors override hierarchy when they apply: `success()` green,
`warning()` yellow, `error()` red.

**Never use the same color for adjacent hierarchy levels** — if headers and
items are both blue, they blend together. **Avoid the ANSI dim attribute**
(`\x1b[2m`, standard or bright) — too dark to read on a black terminal
background. **Do not rely on bold alone** for a distinction some
terminal/font combinations render identically to normal weight — pair it
with a color difference.
