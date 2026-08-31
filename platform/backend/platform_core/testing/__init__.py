"""Shared pytest fixtures and helpers. Apps import these via a one-line conftest:

    from platform_core.testing import *  # noqa: F401,F403
"""

import pytest
from fastapi.testclient import TestClient

from platform_core import audit
from platform_core.auth import MOCK_USERS, Role
from platform_core.db import use_file_db, use_memory_db
from platform_core.http import ToolConfig, create_app


@pytest.fixture(autouse=True)
def fresh_db():
    use_memory_db()
    yield
    use_file_db()


@pytest.fixture
def viewer():
    return MOCK_USERS[Role.VIEWER]


@pytest.fixture
def operator():
    return MOCK_USERS[Role.OPERATOR]


@pytest.fixture
def supervisor():
    return MOCK_USERS[Role.SUPERVISOR]


def make_client(config: ToolConfig) -> TestClient:
    return TestClient(create_app([config]))


def as_role(role: Role) -> dict[str, str]:
    """Headers selecting the mock acting user."""
    return {"X-Mock-Role": role.value}


def assert_audited(
    resource_type: str,
    resource_id: str,
    *,
    action: str,
    outcome: str,
    actor_role: Role | None = None,
) -> None:
    """Assert the most recent matching audit record exists for the resource."""
    records = audit.list_for_resource(resource_type, resource_id)
    for r in records:
        if r.action == action and r.outcome == outcome and (
            actor_role is None or r.actor_role == actor_role.value
        ):
            return
    raise AssertionError(
        f"No audit record for action={action} outcome={outcome} on "
        f"{resource_type}/{resource_id}. Records: {[(r.action, r.outcome) for r in records]}"
    )
