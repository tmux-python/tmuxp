import pytest


@pytest.fixture()
def tmpdir(tmpdir_factory):
    fn = tmpdir_factory.mktemp('tmuxp')
    return fn
