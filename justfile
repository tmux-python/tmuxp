# justfile for tmuxp
# https://just.systems/

set shell := ["bash", "-uc"]

# File patterns
py_files := "find . -type f -not -path '*/\\.*' | grep -i '.*[.]py$' 2> /dev/null"
test_files := "find . -type f -not -path '*/\\.*' | grep -i '.*[.]\\(yaml\\|py\\)$' 2> /dev/null"
doc_files := "find . -type f -not -path '*/\\.*' | grep -i '.*[.]rst$\\|.*[.]md$\\|.*[.]css$\\|.*[.]py$\\|mkdocs\\.yml\\|CHANGES\\|TODO\\|.*conf\\.py' 2> /dev/null"

# List all available commands
default:
    @just --list

# ============================================================================
# Testing
# ============================================================================

# Run tests with pytest
test *args:
    uv run py.test {{ args }}

# Run tests then start continuous testing with pytest-watcher
start:
    just test
    uv run ptw .

# Watch files and run tests on change (requires entr)
watch-test:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v entr > /dev/null; then
        ${{ test_files }} | entr -c just test
    else
        just test
        just _entr-warn
    fi

# ============================================================================
# Documentation
# ============================================================================

# Build documentation
build-docs:
    just -f docs/justfile html

# Watch files and rebuild docs on change
watch-docs:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v entr > /dev/null; then
        ${{ doc_files }} | entr -c just build-docs
    else
        just build-docs
        just _entr-warn
    fi

# Serve documentation
serve-docs:
    just -f docs/justfile serve

# Watch and serve docs simultaneously
dev-docs:
    #!/usr/bin/env bash
    set -euo pipefail
    just watch-docs &
    just serve-docs

# Start documentation server with auto-reload
start-docs:
    just -f docs/justfile start

# Start documentation design mode (watches static files)
design-docs:
    just -f docs/justfile design

# ============================================================================
# Linting & Formatting
# ============================================================================

# Format code with ruff
ruff-format:
    uv run ruff format .

# Run ruff linter
ruff:
    uv run ruff check .

# Watch files and run ruff on change
watch-ruff:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v entr > /dev/null; then
        ${{ py_files }} | entr -c just ruff
    else
        just ruff
        just _entr-warn
    fi

# Run mypy type checker
mypy:
    uv run mypy $(${{ py_files }})

# Watch files and run mypy on change
watch-mypy:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v entr > /dev/null; then
        ${{ py_files }} | entr -c just mypy
    else
        just mypy
        just _entr-warn
    fi

# Format markdown files with prettier
format-markdown:
    npx prettier --parser=markdown -w *.md docs/*.md docs/**/*.md CHANGES

# ============================================================================
# Typing
# ============================================================================

# Run monkeytype to collect runtime types
monkeytype-create:
    uv run monkeytype run $(uv run which py.test)

# Apply collected monkeytype annotations
monkeytype-apply:
    uv run monkeytype list-modules | xargs -n1 -I{} sh -c 'uv run monkeytype apply {}'

# ============================================================================
# Private helpers
# ============================================================================

[private]
_entr-warn:
    @echo "----------------------------------------------------------"
    @echo "     ! File watching functionality non-operational !      "
    @echo "                                                          "
    @echo "Install entr(1) to automatically run tasks on file change."
    @echo "See https://eradman.com/entrproject/                      "
    @echo "----------------------------------------------------------"
