# Writing

How this project writes prose, for humans and agents alike. It governs
`README.md`, `CHANGES`, `MIGRATION`, commit messages, CLI help and error text,
docstrings, source comments, and the documentation pages under `docs/` — every
surface a reader reaches.

For environment setup, the gates, and pull request workflow, see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Voice

Three surfaces, one voice. A docstring says what a caller may rely on; a
`CHANGES` entry says what changed; prose says what happens. All three are
present tense, lead with the thing being described, and stop. Why it was built
that way belongs in the commit message, which is timestamped and attached to
the diff.

The most useful editing operation is deleting the introductory sentence.

Lead with verbs and name concrete things. Put identifiers in backticks. Prefer
short declarative sentences, one operational fact each. Do not explain Python
to Python developers; do explain this project's semantics.

Type annotations describe shape. Documentation describes meaning. A sentence
that restates a signature has said nothing.

Use MUST, SHOULD, and MAY only where the normative sense is meant. Say what
actually happens rather than that something is "supported".

| Instead of                       | Prefer                             |
| --------------------------------- | ----------------------------------- |
| "We added…"                       | "`tmuxp freeze` now accepts…"       |
| "New and improved"                | "`WorkspaceBuilder` now…"           |
| "powerful", "seamless"            | state the capability                |
| "easily", "simply", "just"        | omit                                |
| "simple", "obvious", "intuitive"  | omit                                 |
| "robust"                          | name the failure that is handled    |
| "comprehensive"                   | name what is covered                |
| "production-ready"                | state the guarantee                 |
| "optimized", "blazingly fast"     | give the magnitude                  |
| "various fixes"                   | name the components                 |
| "under the hood"                  | omit unless observable              |
| "please note that", "note that"   | state the fact                      |
| "leverage", "utilize"             | "use"                               |
| "delve into"                      | "read", or omit                     |
| "best practices"                  | name the practice                   |
| "in order to"                     | "to"                                |

## Who you are writing for

The default reader runs tmuxp and writes workspace files in YAML or JSON. They
are fluent in tmux itself — servers, sessions, windows, panes, layouts, the
shell and its prompt — but you cannot assume they read Python, know tmuxp's
internals, or have heard of its builder architecture, entry points, or
`sys.path`. Serve them first.

A second, smaller reader writes Python: custom workspace builders, plugins, or
code against `tmuxp`/[libtmux] directly. Serve them too, but mark their
material opt-in — "for the braver cases", "advanced" — so the default reader
knows they can stop. Never make the common case pay a comprehension tax for the
advanced one.

[libtmux]: https://github.com/tmux-python/libtmux

Rules that follow:

- **Second person, present tense, active.** "You name the builder", not "The
  builder is selected". Address the reader who is doing the thing.
- **Concept before configuration.** Open by saying what the thing *is* and
  what it does for the reader. The YAML surface — the keys, the flags — is the
  last detail they need, not the first. A page that opens with "set these
  keys" has buried the idea under its mechanics.
- **Say when they can stop.** Lead with the default and the reassurance: most
  readers never touch this, it works out of the box, everything here is
  optional. Let a skimmer leave after one paragraph.
- **Grant permission, do not demand attention.** "Reach for this when…" tells
  readers they are in the right place without implying they must read on.
- **Progressive disclosure.** Order by how many readers need it: default → the
  one option a few will tune → swapping the whole thing → writing your own.
  Each step is for a smaller audience than the last.
- **Name the trade-off.** If an option costs something — load time, a slower
  attach — say so, and say what it buys ("a little slower, but the workspace
  is fully prepped before you attach"). State it; do not sell it.
- **Frame by concept, not by mechanism.** Do not call a feature "the keys" or
  "the flags" in prose; that names the implementation surface, which is the
  reader's last concern. Name the concept. The mechanics vocabulary — a `Key`
  / `Type` / `Default` table — is correct in a reference table, and only
  there.

### What stays precise

Warm the framing, never the facts. Resolution-order lists, value tables, exact
error strings, and class or function cross-references carry meaning in their
exact form — leave them alone. The friendly voice belongs in the sentences
*around* a precise block, introducing it, not inside it paraphrasing it into
vagueness.

`docs/configuration/workspace-builders.md` is the worked example: a
concept-first intro, an out-of-the-box reassurance, sections ordered by
shrinking audience, an honest trade-off on the prompt wait, and precise
reference tables left precise.

## README

A README is the shortest path from "what is this?" to competent use, not the
project's autobiography.

The first sentence is a contract. It says what abstraction the reader has been
handed, concretely enough to tell this package apart from the neighbouring
one.

Get to a runnable command before anything the reader can skip. A logo, a
mission statement, and three paragraphs of history in front of the install
line all cost the same thing.

State the minimum Python and tmux versions in prose, not only in badges.
`requires-python` in `pyproject.toml` is the authority for Python; the README
must agree with it.

Examples are executable, not illustrative fiction. Never `tmuxp <some-options>`
— show the real command. See
[Documented examples that run](#documented-examples-that-run) for which blocks
are executed and how to write one that qualifies.

Document the semantic model, not the flag list. `--help` already enumerates
flags; what it cannot say is precedence, filesystem effects, what goes to
stdout versus stderr, and what a non-zero exit means.

State defaults explicitly — defaults are API. State negative guarantees where
they exist: "does not modify your tmux configuration", "never overwrites a
workspace file without `-y`". They establish boundaries faster than any amount
of description.

Headings stay conventional and stable, because people deep-link them. Badges
are few and load-bearing.

## The CLI

`tmuxp` is the one console script this package ships (`tmuxp = 'tmuxp:cli.cli'`
in `pyproject.toml`). Its subcommands — `load`, `freeze`, `convert`, `import`,
`edit`, `ls`, `search`, `shell`, `debug-info` — are argparse subparsers under
`src/tmuxp/cli/`.

**Exit statuses.** `0` success, `1` general error (config validation, a tmux
command failure), `2` usage error (invalid arguments — argparse's own
convention). This is the documented contract; see
[Exit Codes](https://tmuxp.git-pull.com/cli/exit-codes.html). Do not invent a
new code without updating that page.

**stdout vs stderr.** Human-facing text — including errors and warnings — goes
through `tmuxp_echo()` (`tmuxp.log`, re-exported via `tmuxp.cli.utils`) or
`OutputFormatter.emit_text()` (`tmuxp.cli._output`), both of which default to
stdout. Errors are distinguished by a bracketed category tag and color, not by
stream: `colors.error("[Builder Error]") + f" {e}"`. The progress/spinner
display (`tmuxp.cli._progress`) writes to stderr by default, keeping stdout
free for a command's real output.

**Machine-readable output.** Commands that support `--json`/`--ndjson` route
through `OutputFormatter`. In `--ndjson` mode, `emit()` streams one JSON object
per line immediately; in `--json` mode it buffers and `finalize()` writes a
single indented array; `emit_text()` is a no-op in both — a machine mode never
mixes prose into the payload stream. Machine-output behavior for error and
empty-result paths (e.g. `search` with no matches) is not yet defined project
-wide; those paths currently emit styled text through `emit_text()`, which
silently drops in machine modes rather than emitting a structured error.
Document a command's machine-mode behavior explicitly if you add one, rather
than leaving it to this default.

**Destructive operations never happen silently.** `tmuxp freeze` and
`tmuxp convert` prompt before overwriting a workspace file; `-y`/`--yes` skips
the prompt. `tmuxp load` on a session name that is already running offers to
attach — it does not kill or replace the running session. Preserve this
invariant in any documentation of a command that writes or replaces state: say
what triggers the prompt and what flag skips it.

## Workspace files

A workspace file is YAML or JSON describing a tmux session, window, and pane
layout — the domain term is "workspace", never "config" or "session file" in
prose (a "session" is the live tmux object the workspace file builds). `.yaml`
and `.json` are equivalent input formats through `ConfigReader`
(`tmuxp._internal.config_reader`); document a new top-level key for both, and
keep any YAML example convertible with `tmuxp convert`.

Values trickle down the hierarchy — session → window → pane — so a key set at
the session level is a default any window or pane can override. State that
inheritance explicitly wherever a new key is introduced; it is not visible from
the schema alone.

## Documented examples that run

Examples in this repository are tests. This section is the contract for
writing one the test suite can actually see.

**A fence tag is cosmetic. Only a `>>> ` prompt executes.** A block written as

    ```python
    server = Server()
    ```

is prose that looks like a test. Nothing collects it, nothing runs it, and it
can be wrong for years. The same block written with prompts is a test:

    ```python
    >>> server = Server()
    ```

This is the single most expensive mistake available when editing documentation,
because removing the prompts leaves a green test suite and a silently deleted
test. When editing a file that contains examples, count the prompts before and
after.

**The fence tag is `python`.** Not `pycon`, not bare.

**Where examples run.** `[tool.pytest.ini_options]` in `pyproject.toml` sets
`testpaths = ["src/tmuxp", "tests", "docs"]` and `addopts` includes
`--doctest-modules`. That makes every `>>> ` block inside a `src/tmuxp/**`
docstring, and inside any `.py` file under `docs/` (the Sphinx extensions in
`docs/_ext/`), a collected test. **`README.md` is not in `testpaths`.** Its
code blocks, prompted or not, are never executed — write them for a human
reader, and hold them to correctness by review, not by pytest. `docs/*.md`
pages are likewise not doctest-collected; only the `.py` files under `docs/`
are.

**Fixtures available to a doctest.** The root `conftest.py` defines an
autouse `add_doctest_fixtures` fixture. Every doctest gets `test_utils`,
`tmp_path`, and `monkeypatch` in its namespace. A doctest also gets `server`,
`session`, `window`, and `pane` — real tmux objects — **only** when its module
name is in `conftest.py`'s `DOCTEST_NEEDS_TMUX` set, currently
`{"tmuxp.workspace.builder.classic"}`, and only when `tmux` is on `PATH`.
Writing `>>> session.name` in a docstring outside that one module raises
`NameError` at test time; it is not a fixture available repository-wide.
Doctests in `DOCTEST_NEEDS_TMUX` modules are auto-marked
`pytest.mark.flaky(reruns=2)` (via `pytest_collection_modifyitems`) because
real tmux/shell timing is not deterministic. Adding a new module to that set
is how you opt a doctest into live tmux fixtures — do it deliberately, and
expect the flaky marker to apply.

**`# doctest: +SKIP` is not permitted.** It is a workaround that tests nothing.
Use the fixtures, or move the example to `tests/examples/<path>/`.

**Do not downgrade a doctest to a non-executed block to make it pass.** A
`.. code-block::` or an unprompted fence does not run. If an example cannot
pass, fix the example or fix the code.

**Option flags.** `ELLIPSIS` and `NORMALIZE_WHITESPACE` are enabled globally
(`doctest_optionflags` in `pyproject.toml`), so `...` elides variable output —
useful for session/window/pane IDs like `$3` or `@7` — and whitespace
differences do not fail a comparison. Reach for an inline `# doctest: +FLAG`
only for the block that needs something beyond those two.

**Docstring examples** use the NumPy `Examples` section:

    Examples
    --------
    >>> from tmuxp.cli._output import get_output_mode
    >>> get_output_mode(json_flag=True, ndjson_flag=False)
    <OutputMode.JSON: 'json'>

**Doctests are not required everywhere.** Sphinx `setup(app)` entry points
(`docs/_ext/tmux_layout.py`, `docs/_ext/aafig.py`) are not testable in
isolation the way Sphinx and docutils themselves leave their own `setup()`
functions and `visit_*`/`depart_*` node methods untested by example. Extract a
testable helper predicate from a complex recursive traversal function and
doctest that instead of the traversal itself.

**Room to grow.** The docutils collector reads `.md` and `.rst` wherever it is
loaded — currently nowhere in this repository's `testpaths`, since only
`docs/*.py` files are collected under `docs/`. Adding a documentation page's
prompted block to the executed set requires first adding that page's directory
to `testpaths`. The MyST `{doctest}` directive and the reStructuredText
`.. doctest::` directive are available if that is ever adopted; document the
change here when it happens.

## MyST roles

Any class, method, function, exception, or attribute that has its own rendered
API page must be cited via the appropriate role — never with plain backticks:
`{class}`, `{meth}`, `{func}`, `{exc}`, `{attr}`, `{mod}`. Doc pages without an
explicit ref label use `{doc}`; internal section anchors use `{ref}`. Plain
backticks are correct for code syntax, environment variables, parameter names,
and file paths that are not doc pages — anything without an autodoc
destination.

Link the first prose mention of any symbol that has a useful destination on
that page — Python objects, tmuxp or libtmux APIs, CLI command pages, topic
pages, external tools. Use the most specific target available. Do not rely on
a later reference section to satisfy the first-mention rule: if the first
occurrence is a heading or a grid-card teaser, link that occurrence or retitle
so the first prose mention can carry the link. Leave command examples, code
blocks, Mermaid node labels, and literal configuration values as code; link
the surrounding prose instead. After the first linked mention on a page, later
mentions can stay plain unless distance or context makes another link useful.

**Diagrams.** Mermaid diagrams render to inline SVG at build time (via
`sphinx-gp-mermaid`). Tag any node whose label is a command, code identifier,
or config key with `:::cmd` so it renders monospace; leave prose and concept
nodes unstyled. Prefer `flowchart TD` — wide left-to-right charts do not scale
on narrow viewports. Add `:alt:`, `:name:`, and `:responsive: fit` to every
diagram; use `:responsive: preserve` only when the wide artifact is
intentional and should scroll.

**Internal API pages** document a module with an `{eval-rst}` block wrapping
`.. automodule:: <module>` and `:members:`, matching `docs/internals/api/**`. A
bare `.. py:module::` registers a cross-reference target but renders an empty
page — reach for it only on an index page that already carries its own
content (grids, prose) where `automodule` would duplicate members documented
on the leaf pages.

## The changelog

`CHANGES` is the changelog, rendered as the project's changelog page, modeled
on Django's release-notes shape: deliverables get titles and prose, not
bullets.

**Release entry boilerplate.** Every release header is
`## tmuxp X.Y.Z (YYYY-MM-DD)`. The file opens with a
`## tmuxp X.Y.Z (Yet to be released)` placeholder block fenced by
`<!-- KEEP THIS PLACEHOLDER ... -->` and `<!-- END PLACEHOLDER ... -->` HTML
comments — new release entries land immediately below the END marker, never
above it.

**Unreleased entries carry no lead paragraph and no version summary.**
Speaking for a release — what the version "is", "ships", or "focuses on" — is
presumptuous before its scope is final. Only the person cutting the release
writes the lead paragraph, and only once the version and date are set. Never
write or edit a lead paragraph from a feature branch.

**A released entry opens with a multi-sentence lead paragraph.** Plain prose,
no italic. Open with the version as sentence subject ("tmuxp X.Y.Z ships …")
so the lead is self-contained when excerpted. Two to four sentences on what
shipped and who cares — user-visible takeaways, not internal mechanism.
Cross-reference detail docs with `{ref}` to keep the lead compact.

**Each deliverable is a section, not a bullet.** Inside `### What's new`,
every distinct deliverable gets a `#### Deliverable title (#NN)` heading
naming it in user vocabulary, followed by one to three prose paragraphs. Do
not wrap a paragraph in `- ` — bullets are for enumerable lists, not
paragraph containers. Cross-link detail docs ("See {ref}`foo` for details.")
so the entry's prose stays focused.

**The deliverable test.** Before writing an entry, ask: "What's the
deliverable, in user vocabulary?" If you cannot answer in one sentence, the
entry is not ready. Mechanism — helper internals, byte counters,
schema-validation locations — belongs in pull request descriptions and code
comments, not the changelog.

**Fixed subheadings**, in this order when present: `### Breaking changes`,
`### Dependencies`, `### What's new`, `### Fixes`, `### Documentation`,
`### Development`. Dev tooling (helper scripts, internal automation) lives
under `### Development`. A breaking change shows the migration path with
concrete inline code — a `# Before` / `# After` fenced block — not a pointer
to one. Dependency floor bumps use the form
``Minimum `pkg>=X.Y.Z` (was `>=X.Y.W`)``.

**PR refs `(#NN)`** sit in each deliverable's `####` heading.

**When bullets are appropriate.** Catch-all sections (`### Fixes`,
occasionally `### Documentation`) with three or more genuinely small items use
bullets — one line each, never paragraphs. If a bullet swells past two lines,
promote it to a `#### Title (#NN)` heading with a prose body.

**Anti-patterns.** Fragile metrics that go stale silently — token ceilings,
third-party version pins, percent benchmarks, exact byte counts. Describe the
capability, not the math. Internal jargon: private symbols (leading-underscore
identifiers), algorithm names exposed for the first time, backend scaffolding.
Walls of text dressed up as bullets. Breaking changes buried mid-entry instead
of given their own subheading at the top.

**Numbers over adjectives**, where a number is available: "cold start 41 ms to
6 ms" is a sentence; "much faster startup" is a smell.

**Summarization style.** When asked "what changed in the latest version?" or
similar, lead with the entry's lead paragraph (paraphrased if needed),
followed by each `####` deliverable heading under `### What's new` with a
one-sentence summary. Cite `(#NN)` only if asked for source links. Do not
invent versions, dates, or numbers not present in `CHANGES`. Do not quote line
numbers or file offsets — those shift as the file evolves.

Versions are PEP 440 identifiers. Semantic-versioning meaning applies to the
documented public API — command names, options, exit statuses, configuration
keys, environment variables, and serialized workspace formats, not only
imported Python symbols.

## Docstrings

The prime directive: never restate the type. The annotation is the source of
truth; the docstring carries what the annotation cannot.

This is documentation debt wearing a docstring:

    def get_id(pane: Pane) -> str:
        """Get the pane's identifier.

        Parameters
        ----------
        pane : Pane
            The pane.

        Returns
        -------
        str
            The identifier.
        """

Document instead the dimensions the type system cannot encode:

- **Mutation.** What it changes in place.
- **Ownership.** What the caller must close, release, or keep alive.
- **Ordering.** Whether results come back in a guaranteed order.
- **Timing.** What has finished by the time the call returns.
- **Failure.** Which exceptions are raised and what triggers each.
- **Idempotence.** Whether calling twice does anything the second time.
- **Concurrency.** Whether calls are coalesced, queued, or independent.
- **Units and ranges.** What a number means and what values are accepted.
- **Boundary behaviour.** What zero, empty, and the maximum do.
- **Platform.** Behaviour that differs by operating system, tmux version, or
  dependency version.
- **Security boundary.** What is executed, and what is only read — call this
  out explicitly for anything that runs a shell command or `exec`s a string
  (`tmuxp shell -c`, `$PYTHONSTARTUP` sourcing, workspace `shell_command`).

The ambiguity worth resolving by example: whether "retry three times" means
three attempts or four. State it.

The first sentence stands alone; tooling truncates there. PEP 257 applies:
triple double quotes, an imperative one-line summary ending in a period, a
blank line before any extended description. Do not repeat an introspectable
signature.

NumPy-style docstrings (the `pydocstyle` convention ruff enforces) are the one
dialect this repository uses, enforced by the linter rather than relitigated
in review.

**Class-level names** — every name a class declares that autodoc renders gets
exactly one description. That covers `NamedTuple` fields, dataclass fields
including `InitVar`, `TypedDict` keys, `Enum` members, `ClassVar`s, and plain
constants. The shape does not change the rule.

Three styles count: a NumPy `Attributes` entry in the class docstring, a
docstring under the assignment, or a `#:` comment above it. Prefer
`Attributes`:

```python
class SearchToken(t.NamedTuple):
    """Parsed search token with target fields and raw pattern.

    Attributes
    ----------
    fields : tuple[str, ...]
        Canonical field names to search (e.g., ('name', 'session_name')).
    pattern : str
        Raw search pattern before regex compilation.
    """
```

A `Parameters` section does **not** describe attributes — it documents the
initializer, and the attribute entries still render bare beneath it.

A field nobody describes reaches the reference as a bare name. A `ClassVar`
nobody describes is withheld from it entirely, so an undescribed one is
silently missing rather than visibly empty. A field a base class describes is
carried through to the subclass, so an inherited field needs no restatement.

## Source comments

A comment ships only if it passes all three gates. Fail any: delete or
rewrite. Borderline: delete — borderline means the information is
reconstructible, which is what makes deletion cheap.

**Loss.** Three years from now, would losing this cost a maintainer real time
rediscovering intent, an invariant, a constraint, or a failure mode the code
and tests do not already make obvious?

**Elite.** Would SQLite, Redis, the Go standard library, or CPython write this
comment, at this length? Those projects state the constraint and stop. They do
not argue with an imagined objector.

**Upkeep.** Will it stay true without maintenance? A comment that hand-syncs a
value the code owns — a count, an offset, a line reference, a duplicated
constant — is false the first time that value moves.

### Ceiling

One or two lines. A comment reaching four is either carrying several facts, in
which case split it, or arguing, in which case cut it to the fact.

Rationale, alternatives weighed, and the story of how the code got here belong
in the commit message: timestamped, attached to the exact diff, and free to
maintain.

A comment often holds both a constraint and the deliberation that found it.
Keep the constraint, cut the deliberation. "Runs at most once per second"
survives; "this is the right trade for now" does not.

### Keep

- Why over how: upstream tmux quirks, protocol and compatibility constraints,
  performance tradeoffs still part of the contract.
- Invariants, preconditions, ordering, lifetime, and concurrency requirements
  that types and tests cannot express.
- Code that looks wrong but is not, so a later cleanup does not reintroduce
  the bug.
- A high-level sketch of an algorithm whose local operations do not reveal
  the whole.

### Delete

- Narration of the next lines; code translated into English.
- Restated names, types, defaults, or control flow.
- Values duplicated from the code and hand-synced.
- Justification, hedging, or apology for a choice.
- Speculation about future requirements.
- History version control already holds, including commented-out code.
- Ticket and issue numbers. They say nothing to a reader without tracker
  access, and they rot when the tracker moves. Unfinished work goes in the
  tracker, not the source.
- Transient observations — "currently", "for now", "the latest release" —
  that go stale with no nearby edit.

### The upkeep gate in practice

It reaches values that track our own code. It does not reach frozen external
facts.

Bad (Delete):

```python
# There are 321 tests to complete for servers.
```

Good (Keep):

```python
# tmux < 3.2 reports the pane ID only after the command completes,
# so this query must stay separate.
```

### Documentation exception

Minimal usage examples, and parameter, return, and raises entries on public
API are exempt from the loss gate — they serve the caller, not the
maintainer. They are exempt from nothing else. Ceiling: a good man page entry.

## Terminology and capitalization

Pick the domain noun and keep it. "Workspace file" is the YAML/JSON on disk;
"session" is the live tmux object it builds — do not call a workspace file a
"config" in one paragraph and a "session file" in the next. If the method is
`capture_pane`, write "capture" everywhere rather than alternating with
"read", "grab", and "snapshot".

Stable vocabulary is what makes search, deep links, and an agent's retrieval
work at all.

Python and PyPI keep their own capitalisation. Distribution names are written
as they are published.

Do not write counts into prose — how many symbols exist, how many tests there
are. They go stale silently and no reader needs them. Counts that pin a
fixture or guard an invariant are different, and belong in code.

## Markdown

Prose wraps at 80 columns. Table rows, badge lines, and long links are exempt,
because breaking them harms rendering. A pull request or issue body does not
wrap at all: GitHub renders a single newline as a space in a file and as a
line break in a comment, so a wrapped comment body arrives as ragged stubs.

GitHub alert blocks — `> [!NOTE]`, `> [!WARNING]` — render as literal text
outside GitHub, so reserve them for at most one load-bearing warning per
document. Write the sentence so it carries the fact on its own, and a
renderer that drops the marker loses nothing.

Do not use a local absolute path or an email address in anything published.

## Code blocks

Code blocks are paste-and-run units: pasting one block runs exactly one
intended action. Executed examples are exempt — the test suite runs them,
nobody pastes them.

- **One command per block.** Multiple steps may share a block only when
  explicitly chained with `&&`, `;`, or `\` continuations — the chain is then
  one logical command.
- **Explanations go in prose above the block**, never as `#` comments inside
  it.
- **Command menus are per-command blocks with prose lead-ins**, not tables.
- **Shell commands use the `console` tag with a `$ ` prefix.** This separates
  interactive commands from scripts and enables prompt-aware copy.
- **Split long commands with `\`** — one flag or flag+value pair per indented
  continuation line, positional arguments last.

Good — show the last ten commits as a graph:

```console
$ git log \
    --max-count=10 \
    --graph \
    --oneline
```

Bad:

```console
# Show the last ten commits as a graph
$ git log --max-count=10 --graph --oneline
```

## Commits

```
Scope(type[detail]): concise description

why: Explanation of necessity or impact.

what:
- Specific technical changes made
- Focused on a single topic
```

Keep the subject to 50 characters or fewer, excluding any trailing `(#NN)`
pull request reference, and wrap body lines at 72. Separate the `why:` and
`what:` blocks with a blank line.

Routine maintenance commits drop the colon and take a capitalised
description, which is what distinguishes them at a glance in
`git log --oneline`:

```
py(deps[dev]) Bump dev packages
ai(rules[AGENTS]) Judge comments by three gates
```

Everything that changes behaviour keeps the colon.

Common types:

- **feat**: New features or enhancements
- **fix**: Bug fixes
- **refactor**: Code restructuring without functional change
- **docs**: Documentation updates
- **chore**: Maintenance (dependencies, tooling, config)
- **test**: Test-related updates
- **style**: Code style and formatting
- **ci**: Workflow and pipeline changes
- **py(deps)**: Dependencies
- **py(deps[dev])**: Dev dependencies
- **ai(rules[AGENTS])**: AI rule updates (`AGENTS.md`, `CLAUDE.md`)
- **ai(claude[command])**: Claude Code command or skill changes (`.claude/`)

Example:

```
Pane(feat[send_keys]): Add support for a literal flag

why: Send characters without tmux interpreting them.

what:
- Add a literal parameter to send_keys
- Pass -l when it is set
```

For a multi-line message, use a heredoc so the formatting survives:

```console
$ git commit -m "$(cat <<'EOF'
Scope(feat[detail]): Concise description

why: Explanation of the change.

what:
- First change
- Second change
EOF
)"
```

### Release commits

Never create tags. Never push tags. The owner handles tagging and tag pushes,
because a tag triggers the publish workflow.

A release commit subject is plain and short: `Tag v<version>`. The detailed
why and what go in the body. Do not use the `Scope(type[detail]):` format for
a release — it buries the lede.

## Slop prevention

Treat AI slop as review-hostile noise, not as proof that text or code is
wrong. The goal is to maximise information density.

- **AI signatures.** No "Generated by", no conversational filler, no
  unexplained emoji, no tool metadata.
- **Brittle references.** No hard-coded line numbers, fragile file counts,
  dated "as of" claims, bare SHAs, or local absolute paths — unless they are
  strict evidentiary artefacts such as a benchmark log.
- **Diff narration.** Do not restate what moved, was renamed, or was removed
  in anything the reader holds alongside the diff: code, docstrings, README,
  `CHANGES`, or a pull request description. The diff and commit message
  already carry it.
- **Branch-internal narrative.** Do not mention intermediate states,
  abandoned approaches, or "no longer" behaviour unless users of a published
  release actually experienced the old state — **the published-release
  test**. When cleaning up in hindsight on a long-running branch, diff against
  trunk (not an intermediate state on the same branch) to find what the
  branch actually introduced, and default to leaving trunk history alone.
- **Low-value scaffolding.** No ownerless TODOs, unused future-proofing,
  debug artefacts, or defensive wrappers around failure modes nothing can
  reach.
- **Prose inflation.** The diction table under [Voice](#voice) governs;
  replace an inflated word with a concrete description of behaviour,
  constraints, or trade-offs.
- **Coded labels.** Write rules and findings as plain imperatives. No `[R1]`,
  `Option B`, or any index a reader has to decode.

Preserve the "why". Never delete a comment documenting an invariant, a
protocol constraint, a platform quirk, or an upstream workaround — those are
the facts [Source comments](#source-comments) keeps, and every other comment
is judged by it.

**Durable source links.** Link to a pinned revision, never to trunk. A pinned
permalink is not a brittle reference; an unlinked SHA dropped into prose is.
`blob/master/…` links rot silently — the file moves, lines shift, and the
anchor lands on unrelated code while still resolving.

- Prefer a release tag (`blob/v1.74.0/…`). Most durable, and it tells the
  reader which released version the claim held for.
- Otherwise use a 7-character commit ref (`blob/9a29b1a/…`) reachable from
  `master`. Use when there is no tag or the claim is about unreleased code.
  Never a pull-request-head SHA — it can be rebased or garbage-collected.
- Reserve `blob/master/…` for living documents meant to always show the
  latest state, such as this contributing guide.
- Line anchors (`#L120-L145`) are only safe on a pinned ref.
