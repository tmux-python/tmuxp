from tmux import t
from . import TestTmux


class TestSessions(TestTmux):
    def test_has_session(self):
        assert t.has_session(self.TEST_SESSION_NAME) is True
        assert t.has_session('asdf2314324321') is False
