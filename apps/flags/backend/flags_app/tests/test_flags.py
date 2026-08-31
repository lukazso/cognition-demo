"""Permissions, transitions, preconditions, idempotency, and audit for the flags tool."""

import uuid

from platform_core.auth import Role
from platform_core.connectors import ErrKind
from platform_core.testing import as_role, assert_audited

DRAFT = "flag-1004"  # draft
STAGING_ONLY = "flag-1002"  # active, prod off
PROD_10 = "flag-1001"  # active, prod on at 10%
PROD_50 = "flag-1003"  # active, prod on at 50%
ARCHIVED = "flag-1010"


def _invoke(client, flag_id: str, action: str, role: Role, input_data: dict | None = None,
            key: str | None = None):
    return client.post(
        f"/api/flags/resources/{flag_id}/actions/{action}",
        json={"idempotency_key": key or str(uuid.uuid4()), "input": input_data or {}},
        headers=as_role(role),
    )


def _get(client, flag_id: str, role: Role = Role.VIEWER):
    return client.get(f"/api/flags/resources/{flag_id}", headers=as_role(role)).json()


def _create(client, role: Role, input_data: dict, key: str | None = None):
    return client.post(
        "/api/flags/resources/actions/create",
        json={"idempotency_key": key or str(uuid.uuid4()), "input": input_data},
        headers=as_role(role),
    )


NEW_FLAG = {"key": "search.semantic-ranking", "description": "Semantic ranking", "owner_team": "search"}


class TestCreate:
    def test_operator_creates_a_draft_flag(self, client):
        response = _create(client, Role.OPERATOR, NEW_FLAG)
        assert response.status_code == 200
        flag = response.json()["resource"]
        assert (flag["state"], flag["staging_enabled"], flag["prod_enabled"],
                flag["prod_rollout_pct"]) == ("draft", False, False, 0)
        assert_audited("feature_flag", response.json()["resource_id"], action="flags.create",
                       outcome="success", actor_role=Role.OPERATOR)

    def test_viewer_cannot_create(self, client):
        assert _create(client, Role.VIEWER, NEW_FLAG).status_code == 403
        assert client.get("/api/flags/resources", headers=as_role(Role.VIEWER)).json()["total"] == 12

    def test_duplicate_key_rejected(self, client):
        response = _create(client, Role.OPERATOR,
                           {**NEW_FLAG, "key": "checkout.new-payment-flow"})
        assert response.status_code == 502
        assert client.get("/api/flags/resources", headers=as_role(Role.VIEWER)).json()["total"] == 12

    def test_missing_fields_rejected(self, client):
        assert _create(client, Role.OPERATOR, {"key": "a.b"}).status_code == 422

    def test_replay_creates_one_flag(self, client):
        key = str(uuid.uuid4())
        first = _create(client, Role.OPERATOR, NEW_FLAG, key=key)
        replay = _create(client, Role.OPERATOR, NEW_FLAG, key=key)
        assert replay.json()["replayed"] is True
        assert replay.json()["resource_id"] == first.json()["resource_id"]
        assert client.get("/api/flags/resources", headers=as_role(Role.VIEWER)).json()["total"] == 13

    def test_create_is_advertised_by_role_only(self, client):
        listing = client.get("/api/flags/resources", headers=as_role(Role.OPERATOR)).json()
        assert listing["available_create_actions"] == ["flags.create"]
        assert client.get("/api/flags/resources", headers=as_role(Role.VIEWER)).json()[
            "available_create_actions"
        ] == []

    def test_new_flag_can_be_activated(self, client):
        flag_id = _create(client, Role.OPERATOR, NEW_FLAG).json()["resource_id"]
        assert _invoke(client, flag_id, "activate", Role.OPERATOR).json()["new_state"] == "active"


class TestPermissions:
    def test_role_matrix(self, client):
        matrix = [
            ("activate", DRAFT, Role.VIEWER, {}, 403),
            ("activate", DRAFT, Role.OPERATOR, {}, 200),
            ("set_staging", STAGING_ONLY, Role.VIEWER, {"enabled": True}, 403),
            ("set_staging", STAGING_ONLY, Role.OPERATOR, {"enabled": False}, 200),
            ("set_production", STAGING_ONLY, Role.OPERATOR, {"enabled": True, "reason": "r"}, 403),
            ("set_production", STAGING_ONLY, Role.SUPERVISOR, {"enabled": True, "reason": "r"}, 200),
            ("set_rollout", PROD_10, Role.OPERATOR, {"percentage": 20, "reason": "r"}, 403),
            ("set_rollout", PROD_10, Role.SUPERVISOR, {"percentage": 20, "reason": "r"}, 200),
            ("archive", STAGING_ONLY, Role.OPERATOR, {"note": "n"}, 403),
        ]
        for action, flag_id, role, input_data, expected in matrix:
            response = _invoke(client, flag_id, action, role, input_data)
            assert response.status_code == expected, (action, role, response.json())

    def test_viewer_can_read(self, client):
        assert client.get("/api/flags/resources", headers=as_role(Role.VIEWER)).status_code == 200
        detail = _get(client, PROD_10)
        assert detail["resource"]["prod_rollout_pct"] == 10
        assert detail["available_actions"] == []

    def test_available_actions_respect_role_and_state(self, client):
        assert _get(client, STAGING_ONLY, Role.OPERATOR)["available_actions"] == [
            "flags.set_staging"
        ]
        assert set(_get(client, STAGING_ONLY, Role.SUPERVISOR)["available_actions"]) == {
            "flags.set_staging",
            "flags.set_production",
            "flags.set_rollout",
            "flags.archive",
        }
        assert _get(client, DRAFT, Role.SUPERVISOR)["available_actions"] == ["flags.activate"]

    def test_archived_flag_is_read_only(self, client):
        assert _get(client, ARCHIVED, Role.SUPERVISOR)["available_actions"] == []
        assert _invoke(client, ARCHIVED, "set_staging", Role.SUPERVISOR,
                       {"enabled": True}).status_code == 409


class TestTransitions:
    def test_draft_flag_activated_by_operator(self, client):
        response = _invoke(client, DRAFT, "activate", Role.OPERATOR)
        assert response.status_code == 200
        assert response.json()["new_state"] == "active"
        assert_audited("feature_flag", DRAFT, action="flags.activate", outcome="success",
                       actor_role=Role.OPERATOR)

    def test_rollout_journey(self, client):
        assert _invoke(client, STAGING_ONLY, "set_staging", Role.OPERATOR,
                       {"enabled": True}).status_code == 200
        assert _invoke(client, STAGING_ONLY, "set_production", Role.SUPERVISOR,
                       {"enabled": True, "reason": "canary"}).status_code == 200
        assert _invoke(client, STAGING_ONLY, "set_rollout", Role.SUPERVISOR,
                       {"percentage": 100, "reason": "full rollout"}).status_code == 200
        flag = _get(client, STAGING_ONLY)["resource"]
        assert flag == {**flag, "prod_enabled": True, "prod_rollout_pct": 100,
                        "change_note": "full rollout", "updated_by": "u-supervisor"}

    def test_activate_rejected_when_already_active(self, client):
        response = _invoke(client, PROD_10, "activate", Role.OPERATOR)
        assert response.status_code == 409
        assert response.json()["detail"]["outcome"] == "invalid_transition"

    def test_archive_requires_production_off(self, client):
        response = _invoke(client, PROD_10, "archive", Role.SUPERVISOR, {"note": "cleaned up"})
        assert response.status_code == 502
        assert _get(client, PROD_10)["resource"]["state"] == "active"
        assert_audited("feature_flag", PROD_10, action="flags.archive", outcome="upstream_failure")

    def test_archive_succeeds_once_production_is_off(self, client):
        assert _invoke(client, PROD_10, "set_production", Role.SUPERVISOR,
                       {"enabled": False, "reason": "code removed"}).status_code == 200
        response = _invoke(client, PROD_10, "archive", Role.SUPERVISOR, {"note": "cleaned up"})
        assert response.status_code == 200
        assert response.json()["new_state"] == "archived"

    def test_rollout_requires_production_on(self, client):
        response = _invoke(client, STAGING_ONLY, "set_rollout", Role.SUPERVISOR,
                           {"percentage": 25, "reason": "ramp"})
        assert response.status_code == 502
        assert _get(client, STAGING_ONLY)["resource"]["prod_rollout_pct"] == 0

    def test_disabling_production_resets_rollout(self, client):
        _invoke(client, PROD_50, "set_production", Role.SUPERVISOR,
                {"enabled": False, "reason": "regression"})
        assert _get(client, PROD_50)["resource"]["prod_rollout_pct"] == 0

    def test_unknown_resource(self, client):
        assert _invoke(client, "flag-9999", "activate", Role.OPERATOR).status_code == 404


class TestValidation:
    def test_rollout_percentage_out_of_range_rejected(self, client):
        response = _invoke(client, PROD_10, "set_rollout", Role.SUPERVISOR,
                           {"percentage": 140, "reason": "oops"})
        assert response.status_code == 422
        assert _get(client, PROD_10)["resource"]["prod_rollout_pct"] == 10
        assert_audited("feature_flag", PROD_10, action="flags.set_rollout", outcome="invalid_input")

    def test_rollout_without_reason_rejected(self, client):
        response = _invoke(client, PROD_10, "set_rollout", Role.SUPERVISOR, {"percentage": 20})
        assert response.status_code == 422
        assert _get(client, PROD_10)["resource"]["prod_rollout_pct"] == 10

    def test_production_change_without_reason_rejected(self, client):
        assert _invoke(client, PROD_10, "set_production", Role.SUPERVISOR,
                       {"enabled": False, "reason": ""}).status_code == 422

    def test_archive_without_note_rejected(self, client):
        assert _invoke(client, STAGING_ONLY, "archive", Role.SUPERVISOR, {}).status_code == 422


class TestIdempotency:
    def test_replay_returns_recorded_outcome_without_reexecuting(self, client):
        key = str(uuid.uuid4())
        first = _invoke(client, PROD_10, "set_rollout", Role.SUPERVISOR,
                        {"percentage": 30, "reason": "ramp"}, key=key)
        assert first.status_code == 200 and first.json()["replayed"] is False
        replay = _invoke(client, PROD_10, "set_rollout", Role.SUPERVISOR,
                         {"percentage": 30, "reason": "ramp"}, key=key)
        assert replay.status_code == 200 and replay.json()["replayed"] is True
        assert _get(client, PROD_10)["resource"]["prod_rollout_pct"] == 30

    def test_key_reuse_across_actions_rejected(self, client):
        key = str(uuid.uuid4())
        assert _invoke(client, DRAFT, "activate", Role.OPERATOR, key=key).status_code == 200
        assert _invoke(client, DRAFT, "set_staging", Role.OPERATOR, {"enabled": True},
                       key=key).status_code == 422


class TestAudit:
    def test_denial_is_audited(self, client):
        _invoke(client, STAGING_ONLY, "set_production", Role.OPERATOR,
                {"enabled": True, "reason": "r"})
        assert_audited("feature_flag", STAGING_ONLY, action="flags.set_production",
                       outcome="permission_denied", actor_role=Role.OPERATOR)
        assert _get(client, STAGING_ONLY)["resource"]["prod_enabled"] is False

    def test_invalid_transition_is_audited(self, client):
        _invoke(client, ARCHIVED, "archive", Role.SUPERVISOR, {"note": "again"})
        assert_audited("feature_flag", ARCHIVED, action="flags.archive",
                       outcome="invalid_transition")

    def test_upstream_failure_is_audited(self, client, tool):
        tool.connector.fail_next(ErrKind.TIMEOUT)
        assert _invoke(client, DRAFT, "activate", Role.OPERATOR).status_code == 502
        assert_audited("feature_flag", DRAFT, action="flags.activate", outcome="upstream_failure")

    def test_state_change_is_audited_before_and_after(self, client):
        _invoke(client, DRAFT, "activate", Role.OPERATOR)
        record = next(
            r for r in _get(client, DRAFT)["audit"]
            if r["action"] == "flags.activate" and r["outcome"] == "success"
        )
        assert (record["before_state"], record["after_state"]) == ("draft", "active")

    def test_field_change_is_audited_with_actor(self, client):
        _invoke(client, PROD_10, "set_rollout", Role.SUPERVISOR,
                {"percentage": 75, "reason": "ramp up"})
        record = next(
            r for r in _get(client, PROD_10)["audit"] if r["action"] == "flags.set_rollout"
        )
        assert record["outcome"] == "success"
        assert record["actor_id"] == "u-supervisor"
        assert (record["before_state"], record["after_state"]) == ("active", "active")
