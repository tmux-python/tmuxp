"""Pytest configuration for tmuxp workspace tests."""
import types

import pytest

from ..fixtures.structures import WorkspaceTestData


@pytest.fixture
def config_fixture() -> WorkspaceTestData:
    """Deferred import of tmuxp.tests.fixtures.*.

    pytest setup (conftest.py) patches os.environ["HOME"], delay execution of
    os.path.expanduser until here.
    """
    from ..fixtures import workspace as test_workspace_data

    return WorkspaceTestData(
        **{
            k: v
            for k, v in test_workspace_data.__dict__.items()
            if isinstance(v, types.ModuleType)
        },
    )
