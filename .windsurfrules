# libtmux Python Project Rules

<project_stack>
- uv - Python package management and virtual environments
- ruff - Fast Python linter and formatter
- py.test - Testing framework
  - pytest-watcher - Continuous test runner
- mypy - Static type checking
- doctest - Testing code examples in documentation
</project_stack>

<coding_style>
- Use a consistent coding style throughout the project
- Format code with ruff before committing
- Run linting and type checking before finalizing changes
- Verify tests pass after each significant change
</coding_style>

<python_docstrings>
- Use reStructuredText format for all docstrings in src/**/*.py files
- Keep the main description on the first line after the opening `"""`
- Use NumPy docstyle for parameter and return value documentation
- Format docstrings as follows:
  ```python
  """Short description of the function or class.

  Detailed description using reStructuredText format.

  Parameters
  ----------
  param1 : type
      Description of param1
  param2 : type
      Description of param2

  Returns
  -------
  type
      Description of return value
  """
  ```
</python_docstrings>

<python_doctests>
- Use narrative descriptions for test sections rather than inline comments
- Format doctests as follows:
  ```python
  """
  Examples
  --------
  Create an instance:

  >>> obj = ExampleClass()
  
  Verify a property:
  
  >>> obj.property
  'expected value'
  """
  ```
- Add blank lines between test sections for improved readability
- Keep doctests simple and focused on demonstrating usage
- Move complex examples to dedicated test files at tests/examples/<path_to_module>/test_<example>.py
- Utilize pytest fixtures via doctest_namespace for complex scenarios
</python_doctests>

<testing_practices>
- Run tests with `uv run py.test` before committing changes
- Use pytest-watcher for continuous testing: `uv run ptw . --now --doctest-modules`
- Fix any test failures before proceeding with additional changes
</testing_practices>

<git_workflow>
- Make atomic commits with conventional commit messages
- Start with an initial commit of functional changes
- Follow with separate commits for formatting, linting, and type checking fixes
</git_workflow>

<git_commit_standards>
- Use the following commit message format:
  ```
  Component/File(commit-type[Subcomponent/method]): Concise description

  why: Explanation of necessity or impact.
  what:
  - Specific technical changes made
  - Focused on a single topic

  refs: #issue-number, breaking changes, or relevant links
  ```

- Common commit types:
  - **feat**: New features or enhancements
  - **fix**: Bug fixes
  - **refactor**: Code restructuring without functional change
  - **docs**: Documentation updates
  - **chore**: Maintenance (dependencies, tooling, config)
  - **test**: Test-related updates
  - **style**: Code style and formatting

- Prefix Python package changes with:
  - `py(deps):` for standard packages
  - `py(deps[dev]):` for development packages
  - `py(deps[extra]):` for extras/sub-packages

- General guidelines:
  - Subject line: Maximum 50 characters
  - Body lines: Maximum 72 characters
  - Use imperative mood (e.g., "Add", "Fix", not "Added", "Fixed")
  - Limit to one topic per commit
  - Separate subject from body with a blank line
  - Mark breaking changes clearly: `BREAKING:`
</git_commit_standards>

<pytest_testing_guidelines>
- Use fixtures from conftest.py instead of monkeypatch and MagicMock when available
- For libtmux tests, use these provided fixtures for fast, efficient tmux resource management:
  - `server`: Creates a temporary tmux server with isolated socket
  - `session`: Creates a temporary tmux session in the server
  - `window`: Creates a temporary tmux window in the session
  - `pane`: Creates a temporary tmux pane in the pane
  - `TestServer`: Factory for creating multiple independent servers with unique socket names
- Example usage with server fixture:
  ```python
  def test_something_with_server(server):
      # server is already running with proper configuration
      my_session = server.new_session("test-session")
      assert server.is_alive()
  ```
- Example usage with session fixture:
  ```python
  def test_something_with_session(session):
      # session is already created and configured
      new_window = session.new_window("test-window")
      assert new_window in session.windows
  ```
- Customize session parameters by overriding the session_params fixture:
  ```python
  @pytest.fixture
  def session_params():
      return {
          'x': 800,
          'y': 600,
          'window_name': 'custom-window'
      }
  ```
- Benefits of using libtmux fixtures:
  - No need to manually set up and tear down tmux infrastructure
  - Tests run in isolated tmux environments
  - Faster test execution
  - Reliable test environment with predictable configuration
- Document in test docstrings why standard fixtures weren't used for exceptional cases
- Use tmp_path (pathlib.Path) fixture over Python's tempfile
- Use monkeypatch fixture over unittest.mock
</pytest_testing_guidelines>

<import_guidelines>
- Prefer namespace imports over importing specific symbols
- Import modules and access attributes through the namespace:
  - Use `import enum` and access `enum.Enum` instead of `from enum import Enum`
  - This applies to standard library modules like pathlib, os, and similar cases
- For typing, use `import typing as t` and access via the namespace:
  - Access typing elements as `t.NamedTuple`, `t.TypedDict`, etc.
  - Note primitive types like unions can be done via `|` pipes
  - Primitive types like list and dict can be done via `list` and `dict` directly
- Benefits of namespace imports:
  - Improves code readability by making the source of symbols clear
  - Reduces potential naming conflicts
  - Makes import statements more maintainable
</import_guidelines>
