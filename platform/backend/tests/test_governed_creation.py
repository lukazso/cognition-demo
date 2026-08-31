"""Governed creation: an action that has no resource yet still goes through the
same authorize -> idempotency -> validate -> execute -> audit pipeline."""

import uuid

import pytest
from pydantic import BaseModel, Field

from platform_core.actions import ALL_ROLES, PENDING_RESOURCE_ID, Action
from platform_core.auth import Role
from platform_core.connectors import Command, Err, ErrKind, FakeConnector
from platform_core.http import ToolConfig
from platform_core.testing import *  # noqa: F401,F403
from platform_core.testing import as_role, assert_audited, make_client


class CreateWidgetInput(BaseModel):
    label: str = Field(min_length=1)


class RenameWidgetInput(BaseModel):
    label: str = Field(min_length=1)


class WidgetConnector(FakeConnector):
    resource_type = "widget"

    def __init__(self) -> None:
        super().__init__()
        self.records["widget-1"] = {"id": "widget-1", "label": "seeded", "state": "active"}

    def build_record(self, command: Command) -> dict | Err:
        label = command.payload["label"]
        if any(r["label"] == label for r in self.records.values()):
            return Err(kind=ErrKind.CONFLICT, message=f"label {label} already used")
        return {"id": f"widget-{len(self.records) + 1}", "label": label, "state": "active"}

    def apply_command(self, record: dict, command: Command) -> Err | None:
        record["label"] = command.payload["label"]
        return None


CREATE = Action(
    name="widgets.create",
    command="create",
    allowed_roles=frozenset({Role.OPERATOR, Role.SUPERVISOR}),
    creates_resource=True,
    input_schema=CreateWidgetInput,
)
RENAME = Action(
    name="widgets.rename",
    command="rename",
    allowed_roles=frozenset({Role.SUPERVISOR}),
    valid_from_states=frozenset({"active"}),
    input_schema=RenameWidgetInput,
)


@pytest.fixture
def tool():
    return ToolConfig(
        tool_id="widgets", connector=WidgetConnector(), actions=[CREATE, RENAME],
        read_roles=ALL_ROLES,
    )


@pytest.fixture
def client(tool):
    return make_client(tool)


def _create(client, role: Role, input_data: dict, key: str | None = None):
    return client.post(
        "/api/widgets/resources/actions/create",
        json={"idempotency_key": key or str(uuid.uuid4()), "input": input_data},
        headers=as_role(role),
    )


def test_create_assigns_id_and_returns_resource(client):
    response = _create(client, Role.OPERATOR, {"label": "fresh"})
    assert response.status_code == 200
    body = response.json()
    assert body["resource_id"] == "widget-2"
    assert body["resource"] == {"id": "widget-2", "label": "fresh", "state": "active"}
    assert client.get("/api/widgets/resources/widget-2", headers=as_role(Role.VIEWER)).status_code == 200


def test_create_is_audited_against_the_new_id(client):
    _create(client, Role.OPERATOR, {"label": "fresh"})
    assert_audited("widget", "widget-2", action="widgets.create", outcome="success",
                   actor_role=Role.OPERATOR)


def test_denied_create_is_audited_without_a_resource(client):
    assert _create(client, Role.VIEWER, {"label": "nope"}).status_code == 403
    assert_audited("widget", PENDING_RESOURCE_ID, action="widgets.create",
                   outcome="permission_denied", actor_role=Role.VIEWER)
    assert client.get("/api/widgets/resources", headers=as_role(Role.VIEWER)).json()["total"] == 1


def test_invalid_input_is_audited_and_creates_nothing(client):
    assert _create(client, Role.OPERATOR, {"label": ""}).status_code == 422
    assert_audited("widget", PENDING_RESOURCE_ID, action="widgets.create", outcome="invalid_input")
    assert client.get("/api/widgets/resources", headers=as_role(Role.VIEWER)).json()["total"] == 1


def test_connector_rejection_is_audited(client):
    response = _create(client, Role.OPERATOR, {"label": "seeded"})
    assert response.status_code == 502
    assert_audited("widget", PENDING_RESOURCE_ID, action="widgets.create",
                   outcome="upstream_failure")


def test_replay_does_not_create_twice(client):
    key = str(uuid.uuid4())
    first = _create(client, Role.OPERATOR, {"label": "fresh"}, key=key)
    replay = _create(client, Role.OPERATOR, {"label": "fresh"}, key=key)
    assert first.json()["replayed"] is False and replay.json()["replayed"] is True
    assert replay.json()["resource_id"] == first.json()["resource_id"]
    assert client.get("/api/widgets/resources", headers=as_role(Role.VIEWER)).json()["total"] == 2


def test_create_actions_are_advertised_by_role_and_kept_off_resources(client):
    listing = client.get("/api/widgets/resources", headers=as_role(Role.OPERATOR)).json()
    assert listing["available_create_actions"] == ["widgets.create"]
    assert client.get("/api/widgets/resources", headers=as_role(Role.VIEWER)).json()[
        "available_create_actions"
    ] == []
    detail = client.get("/api/widgets/resources/widget-1", headers=as_role(Role.SUPERVISOR)).json()
    assert detail["available_actions"] == ["widgets.rename"]


def test_routes_do_not_cross(client):
    # a creating action is not invocable against an existing resource, and vice versa
    assert client.post(
        "/api/widgets/resources/widget-1/actions/create",
        json={"idempotency_key": str(uuid.uuid4()), "input": {"label": "x"}},
        headers=as_role(Role.OPERATOR),
    ).status_code == 404
    assert client.post(
        "/api/widgets/resources/actions/rename",
        json={"idempotency_key": str(uuid.uuid4()), "input": {"label": "x"}},
        headers=as_role(Role.SUPERVISOR),
    ).status_code == 404
