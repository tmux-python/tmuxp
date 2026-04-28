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

# Run tests with pytest
[group: 'test']
test *args:
    uv run py.test {{ args }}

# Run tests then start continuous testing with pytest-watcher
[group: 'test']
start:
    just test
    uv run ptw .

# Watch files and run tests on change (requires entr)
[group: 'test']
watch-test:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v entr > /dev/null; then
        {{ test_files }} | entr -c just test
    else
        just test
        just _entr-warn
    fi

# Run the test suite with the libtmux subprocess engine (default behavior)
[group: 'engines']
test-subprocess *args:
    LIBTMUX_ENGINE=subprocess uv run py.test --engine=subprocess {{ args }}

# Run the test suite with the libtmux imsg (binary protocol) engine
[group: 'engines']
test-imsg *args:
    LIBTMUX_ENGINE=imsg uv run py.test --engine=imsg {{ args }}

# Run the full suite under both engines sequentially and stop on first failure
[group: 'engines']
test-engines *args:
    @echo "===> subprocess engine"
    just test-subprocess {{ args }}
    @echo "===> imsg engine"
    just test-imsg {{ args }}

# Benchmark the test suite under both engines and print a side-by-side summary
[group: 'engines']
bench-engines *args:
    #!/usr/bin/env bash
    set -uo pipefail
    set -- {{ args }}

    report=$(mktemp)
    trap 'rm -f "$report"' EXIT

    bench_engine() {
        local engine="$1"; shift
        local log start end elapsed summary status
        log=$(mktemp)
        echo "===> running with $engine engine"
        start=$(date +%s.%N)
        LIBTMUX_ENGINE="$engine" uv run py.test \
            --engine="$engine" \
            --no-header --tb=no -q --no-cov \
            "$@" 2>&1 | tee "$log"
        status=${PIPESTATUS[0]}
        end=$(date +%s.%N)
        elapsed=$(awk "BEGIN { printf \"%.2f\", $end - $start }")
        summary=$(grep -E "passed|failed|error" "$log" | tail -1 | sed 's/^=*//;s/=*$//;s/^ *//;s/ *$//')
        rm -f "$log"
        printf "%s\t%s\t%s\t%s\n" "$engine" "$elapsed" "$status" "$summary" >> "$report"
    }

    bench_engine subprocess "$@"
    bench_engine imsg "$@"

    echo
    echo "============================== engine benchmark =============================="
    printf "  %-12s %10s  %-7s  %s\n" "engine" "wall (s)" "exit" "summary"
    printf "  %-12s %10s  %-7s  %s\n" "------" "--------" "----" "-------"
    while IFS=$'\t' read -r engine elapsed status summary; do
        if [ "$status" = "0" ]; then
            label=ok
        else
            label="FAIL"
        fi
        printf "  %-12s %10s  %-7s  %s\n" "$engine" "$elapsed" "$label" "$summary"
    done < "$report"
    echo "=============================================================================="

# Build documentation
[group: 'docs']
build-docs:
    just -f docs/justfile html

# Watch files and rebuild docs on change
[group: 'docs']
watch-docs:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v entr > /dev/null; then
        {{ doc_files }} | entr -c just build-docs
    else
        just build-docs
        just _entr-warn
    fi

# Serve documentation
[group: 'docs']
serve-docs:
    just -f docs/justfile serve

# Watch and serve docs simultaneously
[group: 'docs']
dev-docs:
    #!/usr/bin/env bash
    set -euo pipefail
    just watch-docs &
    just serve-docs

# Start documentation server with auto-reload
[group: 'docs']
start-docs:
    just -f docs/justfile start

# Start documentation design mode (watches static files)
[group: 'docs']
design-docs:
    just -f docs/justfile design

# Format code with ruff
[group: 'lint']
ruff-format:
    uv run ruff format .

# Run ruff linter
[group: 'lint']
ruff:
    uv run ruff check .

# Watch files and run ruff on change
[group: 'lint']
watch-ruff:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v entr > /dev/null; then
        {{ py_files }} | entr -c just ruff
    else
        just ruff
        just _entr-warn
    fi

# Run mypy type checker
[group: 'lint']
mypy:
    uv run mypy $({{ py_files }})

# Watch files and run mypy on change
[group: 'lint']
watch-mypy:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v entr > /dev/null; then
        {{ py_files }} | entr -c just mypy
    else
        just mypy
        just _entr-warn
    fi

# Format markdown files with prettier
[group: 'format']
format-markdown:
    npx prettier --parser=markdown -w *.md docs/*.md docs/**/*.md CHANGES

# Run monkeytype to collect runtime types
[group: 'typing']
monkeytype-create:
    uv run monkeytype run $(uv run which py.test)

# Apply collected monkeytype annotations
[group: 'typing']
monkeytype-apply:
    uv run monkeytype list-modules | xargs -n1 -I{} sh -c 'uv run monkeytype apply {}'

[private]
_entr-warn:
    @echo "----------------------------------------------------------"
    @echo "     ! File watching functionality non-operational !      "
    @echo "                                                          "
    @echo "Install entr(1) to automatically run tasks on file change."
    @echo "See https://eradman.com/entrproject/                      "
    @echo "----------------------------------------------------------"
