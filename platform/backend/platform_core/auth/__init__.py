"""Identity integration point.

``CurrentUserProvider`` is the seam where enterprise SSO (Entra/OIDC) would plug in.
The POC ships only ``MockUserProvider``: the acting user is chosen per-request via the
``X-Mock-Role`` header (set by the UI's RoleSwitcher).
"""

from enum import Enum
from typing import Protocol

from fastapi import Header, HTTPException
from pydantic import BaseModel


class Role(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    SUPERVISOR = "supervisor"


class User(BaseModel):
    id: str
    name: str
    email: str
    role: Role


class CurrentUserProvider(Protocol):
    def resolve(self, mock_role: str | None) -> User: ...


MOCK_USERS: dict[Role, User] = {
    Role.VIEWER: User(id="u-viewer", name="Vera Viewer", email="vera@fintech.test", role=Role.VIEWER),
    Role.OPERATOR: User(
        id="u-operator", name="Oscar Operator", email="oscar@fintech.test", role=Role.OPERATOR
    ),
    Role.SUPERVISOR: User(
        id="u-supervisor", name="Sana Supervisor", email="sana@fintech.test", role=Role.SUPERVISOR
    ),
}


class MockUserProvider:
    def resolve(self, mock_role: str | None) -> User:
        if mock_role is None:
            return MOCK_USERS[Role.VIEWER]
        try:
            return MOCK_USERS[Role(mock_role)]
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=f"Unknown role: {mock_role}") from exc


_provider: CurrentUserProvider = MockUserProvider()


def get_current_user(x_mock_role: str | None = Header(default=None)) -> User:
    """FastAPI dependency yielding the acting user."""
    return _provider.resolve(x_mock_role)
