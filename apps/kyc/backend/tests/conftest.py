import pytest
from platform_core.testing import *  # noqa: F401,F403


@pytest.fixture
def tool():
    """Fresh KYC ToolConfig (and fake system of record) per test."""
    from apps.kyc.backend.config import make_tool

    return make_tool()


@pytest.fixture
def client(tool):
    from platform_core.testing import make_client

    return make_client(tool)
