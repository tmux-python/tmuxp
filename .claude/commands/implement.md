# /implement — Plan and Implement from notes/plan.md

Orchestrates the full implementation workflow: plan → implement → test → verify → commit → document.

## Reference Codebases

- **tmuxinator**: `~/study/ruby/tmuxinator/`
- **teamocil**: `~/study/ruby/teamocil/`
- **tmux**: `~/study/c/tmux/`
- **libtmux**: `~/work/python/libtmux/`
- **tmuxp**: `~/work/python/tmuxp/`

## Workflow

### Phase 1: Planning Mode

1. **Read the plan**: Load `notes/plan.md` to understand what needs to be implemented
2. **Select a task**: Pick the highest priority incomplete item from the plan
3. **Research**:
   - Read relevant tmuxinator/teamocil Ruby source for behavior reference
   - Read libtmux Python source for available APIs
   - Read tmuxp source for integration points
   - **Study existing tests** for similar functionality (see Testing Pattern below)
4. **Create implementation plan**: Design the specific changes needed
5. **Exit planning mode** with the finalized approach

### Phase 2: Implementation

1. **Make changes**: Edit the necessary files
2. **Follow conventions**: Match existing code style, use type hints, add docstrings

### Phase 3: Write Tests

**CRITICAL**: Before running verification, write tests for new functionality.

1. **Find similar tests**: Search `tests/` for existing tests of similar features
2. **Follow the project test pattern** (see Testing Pattern below)
3. **Add test cases**: Cover normal cases, edge cases, and error conditions

### Phase 4: Verification

Run the full QA suite:

```bash
uv run ruff check . --fix --show-fixes
uv run ruff format .
uv run mypy
uv run py.test --reruns 0 -vvv
```

All checks must pass before proceeding.

### Phase 5: Commit Implementation

**Source and tests must be in separate commits.**

1. **Commit source code first**: Implementation changes only (e.g., `fix(cli): Read socket_name/path and config from workspace config`)
2. **Commit tests second**: Test files only (e.g., `tests(cli): Add config key precedence tests for load_workspace`)

Follow the project's commit conventions (e.g., `feat:`, `fix:`, `refactor:` for source; `tests:` or `tests(<scope>):` for tests).

### Phase 6: Update Documentation

1. **Update `notes/completed.md`**: Add entry for what was implemented
   - Date
   - What was done
   - Files changed
   - Any notes or follow-ups

2. **Update `notes/plan.md`**: Mark the item as complete or remove it

3. **Commit notes separately**: Use message like `notes: Mark <feature> as complete`

---

## Testing Pattern

This project uses a consistent test pattern. **Always follow this pattern for new tests.**

### 1. NamedTuple Fixture Class

```python
import typing as t

class MyFeatureTestFixture(t.NamedTuple):
    """Test fixture for my feature tests."""

    # pytest (internal): Test fixture name
    test_id: str

    # test params
    input_value: str
    expected_output: str
    expected_error: str | None = None
```

### 2. Fixture List

```python
TEST_MY_FEATURE_FIXTURES: list[MyFeatureTestFixture] = [
    MyFeatureTestFixture(
        test_id="normal-case",
        input_value="foo",
        expected_output="bar",
    ),
    MyFeatureTestFixture(
        test_id="edge-case-empty",
        input_value="",
        expected_output="",
    ),
    MyFeatureTestFixture(
        test_id="error-case",
        input_value="bad",
        expected_output="",
        expected_error="Invalid input",
    ),
]
```

### 3. Parametrized Test Function

```python
@pytest.mark.parametrize(
    "test",
    TEST_MY_FEATURE_FIXTURES,
    ids=[test.test_id for test in TEST_MY_FEATURE_FIXTURES],
)
def test_my_feature(test: MyFeatureTestFixture) -> None:
    """Test my feature with various inputs."""
    result = my_function(test.input_value)
    assert result == test.expected_output

    if test.expected_error:
        # check error handling
        pass
```

### Key Rules

- **Function tests only** — No `class TestFoo:` groupings (per CLAUDE.md)
- **Use fixtures from `tests/fixtures/`** — Prefer real tmux fixtures over mocks
- **Use `tmp_path`** — Not Python's `tempfile`
- **Use `monkeypatch`** — Not `unittest.mock`

---

## Output

After completion, report:
- What was implemented
- Files changed (including test files)
- Test results summary
- What remains in the plan

## Notes

- If tests fail, fix the issues before committing
- If libtmux changes are needed, note them but don't modify libtmux in this workflow
- One logical change per run — don't implement multiple unrelated items
- **Always write tests** — No implementation is complete without tests
