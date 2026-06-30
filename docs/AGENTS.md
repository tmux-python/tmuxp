# Documentation voice

This file covers the *voice* of prose under `docs/` — how to frame a
feature page so a reader meets the idea before its configuration. It
complements the repository-root `AGENTS.md`, which already governs code
blocks, shell-command formatting, changelog conventions, and MyST
roles. When the two overlap, the root file wins; this one only answers
the question it leaves open: how should the prose sound?

## Who you are writing for

The default reader runs tmuxp and writes workspace files in YAML or
JSON. They are fluent in tmux itself — servers, sessions, windows,
panes, layouts, the shell and its prompt — but you cannot assume they
read Python, know tmuxp's internals, or have heard of its builder
architecture, entry points, or `sys.path`.

A second, smaller reader writes Python: custom builders, plugins, code
against libtmux. Serve them too, but mark their material as opt-in
("for the braver cases", "advanced") so the default reader knows they
can stop. Never make the common case pay a comprehension tax for the
advanced one.

## Voice

- **Second person, present tense, active.** "You name the builder", not
  "The builder is selected". Address the reader who is doing the thing.
- **Concept before configuration.** Open by saying what the thing *is*
  and what it does for the reader. The YAML surface — the keys, the
  flags — is the last detail they need, not the first. A page that
  opens with "set these keys" has buried the idea under its mechanics.
- **Say when they can stop.** Lead with the default and the
  reassurance: most readers never touch this, it works out of the box,
  everything here is optional. Let a skimmer leave after one sentence.
- **Progressive disclosure.** Order by how many readers need it:
  default → the one option a few will tune → swapping the whole thing
  → writing your own. Each step is for a smaller audience than the last.
- **Name the trade-off.** If an option costs something — load time, a
  slower attach — say so, and say what it buys ("a little slower, but
  the workspace is fully prepped before you attach"). State it; don't
  sell it.
- **Frame by concept, not by mechanism.** Don't call a feature "the
  keys" or "the flags" in prose; that names the implementation surface,
  which is the reader's last concern. Name the concept. The mechanics
  vocabulary — a `Key` / `Type` / `Default` table — is correct in a
  reference table, and only there.

## What stays precise

Warm the framing, never the facts. Resolution-order lists, value
tables, exact error strings, and class or function cross-references
carry meaning in their exact form — leave them alone. The friendly
voice belongs in the sentences *around* a precise block, introducing
it, not inside it paraphrasing it into vagueness.

## Cross-references

Point the advanced reader at the deep-dive rather than inlining it, and
put the link where their interest peaks — on the phrase that made them
curious ("write your own") — not as a standalone footnote the eye
skips. Use the MyST roles listed in the root `AGENTS.md`.

## A page that does this

`docs/configuration/workspace-builders.md` is the worked example:
a concept-first intro, an out-of-the-box reassurance, sections ordered
by shrinking audience, an honest trade-off on the prompt wait, and
precise reference tables left precise. Read it before reshaping another
page.

## Diagrams and reference pages

Two mechanical conventions, separate from voice:

- **Mermaid diagrams** render to inline SVG at build time (see
  `docs/_ext`). Tag any node whose label is a command, code identifier,
  config key, or other symbol with `:::cmd` so it renders monospace —
  the way that text reads as code inline; leave prose and concept nodes
  unstyled. Prefer top-to-bottom (`flowchart TD`); wide left-to-right
  charts don't scale on narrow viewports. `docs/configuration/workspace-builders.md`
  is the reference.
- **Internal API pages** document a module with an `{eval-rst}` block
  wrapping `.. automodule:: <module>` (with `:members:`), the way the
  existing `docs/internals/api/**` pages do. A bare `.. py:module::`
  registers a cross-reference target but renders an empty page — reach
  for it only to add a *package* target to an index page that already
  carries its own content (grids, prose), where `automodule` would
  duplicate members documented on the leaf pages.

## Before you commit

- Does the page open with what the feature *is*, or with how to
  configure it?
- Can a reader who needs only the default stop after the first
  paragraph?
- Is anything framed as "the keys/flags" that should be named by
  concept instead?
- Are the advanced and Python-only parts clearly marked opt-in?
- Did you leave every table, error string, and cross-reference exact?
- Are diagram command/symbol nodes tagged `:::cmd`, and is the chart
  vertical unless it has a reason to be wide?
