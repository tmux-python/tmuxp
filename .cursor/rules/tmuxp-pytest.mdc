---
description: Guidelines for using pytest with tmuxp, including libtmux fixtures
globs: tests/**/test_*.py
alwaysApply: true
---

# tmuxp Pytest Guidelines

## Leveraging libtmux fixtures

tmuxp tests can utilize libtmux's pytest fixtures for fast, efficient tmux server, session, window, and pane setup/teardown. These fixtures automatically manage the lifecycle of tmux resources during tests.

### Available fixtures

The following fixtures are available through libtmux's pytest plugin:

- `server`: Creates a temporary tmux server with isolated socket
- `session`: Creates a temporary tmux session in the server
- `window`: Creates a temporary tmux window in the session
- `pane`: Creates a temporary tmux pane in the pane
- `TestServer`: Factory for creating multiple independent servers with unique socket names

### Usage in tests

```python
def test_something_with_server(server):
    # server is already running with proper configuration
    my_session = server.new_session("test-session")
    assert server.is_alive()
    assert my_session in server.sessions

def test_something_with_session(session):
    # session is already created and configured
    new_window = session.new_window("test-window")
    assert new_window in session.windows

def test_with_multiple_servers(TestServer):
    # Create independent servers for comparison tests
    Server1 = TestServer()
    Server2 = TestServer()
    
    server1 = Server1()
    server2 = Server2()
    
    session1 = server1.new_session()
    session2 = server2.new_session()
    
    assert server1.socket_path != server2.socket_path
```

### Customizing session parameters

You can override the `session_params` fixture to customize session creation:

```python
import pytest

@pytest.fixture
def session_params():
    return {
        'x': 800,
        'y': 600,
        'window_name': 'custom-window'
    }
```

### Benefits

- No need to manually set up and tear down tmux infrastructure
- Tests run in isolated tmux environments
- Faster test execution
- Reliable test environment with predictable configuration
- Multiple tests can run in parallel without tmux session conflicts

For more details, see:
- [libtmux pytest plugin documentation](https://libtmux.git-pull.com/pytest-plugin/index.html)
- [libtmux pytest plugin code](https://github.com/tmux-python/libtmux/blob/master/src/libtmux/pytest_plugin.py)
