"""Standard test classes every tool ships: permissions, transitions, idempotency, audit."""

import uuid

from platform_core.auth import Role
from platform_core.connectors import ErrKind
from platform_core.testing import as_role, assert_audited


def _invoke(client, case_id: str, action: str, role: Role, input_data: dict | None = None,
            key: str | None = None):
    return client.post(
        f"/api/kyc/resources/{case_id}/actions/{action}",
        json={"idempotency_key": key or str(uuid.uuid4()), "input": input_data or {}},
        headers=as_role(role),
    )


class TestPermissions:
    def test_role_matrix(self, client):
        matrix = [
            ("start_review", "kyc-1001", Role.VIEWER, 403),
            ("start_review", "kyc-1001", Role.OPERATOR, 200),
            ("approve", "kyc-1003", Role.OPERATOR, 403),
            ("approve", "kyc-1003", Role.SUPERVISOR, 200),
            ("reject", "kyc-1006", Role.VIEWER, 403),
            ("reject", "kyc-1006", Role.SUPERVISOR, 200),
        ]
        for action, case_id, role, expected in matrix:
            input_data = {"reason": "test"} if action in ("reject", "escalate") else {}
            response = _invoke(client, case_id, action, role, input_data)
            assert response.status_code == expected, (action, role, response.json())

    def test_viewer_can_read(self, client):
        assert client.get("/api/kyc/resources", headers=as_role(Role.VIEWER)).status_code == 200
        detail = client.get("/api/kyc/resources/kyc-1001", headers=as_role(Role.VIEWER))
        assert detail.status_code == 200
        assert detail.json()["available_actions"] == []

    def test_available_actions_respect_role_and_state(self, client):
        detail = client.get("/api/kyc/resources/kyc-1003", headers=as_role(Role.OPERATOR)).json()
        assert detail["available_actions"] == ["kyc.escalate"]
        detail = client.get("/api/kyc/resources/kyc-1003", headers=as_role(Role.SUPERVISOR)).json()
        assert set(detail["available_actions"]) == {"kyc.escalate", "kyc.approve", "kyc.reject"}


class TestTransitions:
    def test_full_lifecycle(self, client):
        assert _invoke(client, "kyc-1001", "start_review", Role.OPERATOR).status_code == 200
        assert _invoke(client, "kyc-1001", "escalate", Role.OPERATOR,
                       {"reason": "high risk"}).status_code == 200
        response = _invoke(client, "kyc-1001", "approve", Role.SUPERVISOR, {"note": "verified"})
        assert response.status_code == 200
        assert response.json()["new_state"] == "approved"

    def test_invalid_transition_rejected(self, client):
        # kyc-1009 is already approved; approving again is not a valid transition
        response = _invoke(client, "kyc-1009", "approve", Role.SUPERVISOR)
        assert response.status_code == 409
        assert response.json()["detail"]["outcome"] == "invalid_transition"

    def test_missing_required_input_rejected(self, client):
        response = _invoke(client, "kyc-1003", "reject", Role.SUPERVISOR, {})
        assert response.status_code == 422

    def test_unknown_resource(self, client):
        assert _invoke(client, "kyc-9999", "start_review", Role.OPERATOR).status_code == 404


class TestIdempotency:
    def test_replay_returns_recorded_outcome_without_reexecuting(self, client, tool):
        key = str(uuid.uuid4())
        first = _invoke(client, "kyc-1002", "start_review", Role.OPERATOR, key=key)
        assert first.status_code == 200 and first.json()["replayed"] is False
        replay = _invoke(client, "kyc-1002", "start_review", Role.OPERATOR, key=key)
        assert replay.status_code == 200 and replay.json()["replayed"] is True
        assert replay.json()["new_state"] == "in_review"

    def test_key_reuse_across_actions_rejected(self, client):
        key = str(uuid.uuid4())
        assert _invoke(client, "kyc-1002", "start_review", Role.OPERATOR, key=key).status_code == 200
        response = _invoke(client, "kyc-1002", "escalate", Role.OPERATOR,
                           {"reason": "x"}, key=key)
        assert response.status_code == 422


class TestAudit:
    def test_success_is_audited(self, client):
        _invoke(client, "kyc-1004", "start_review", Role.OPERATOR)
        assert_audited("kyc_case", "kyc-1004", action="kyc.start_review", outcome="success",
                       actor_role=Role.OPERATOR)

    def test_denial_is_audited(self, client):
        _invoke(client, "kyc-1004", "start_review", Role.VIEWER)
        assert_audited("kyc_case", "kyc-1004", action="kyc.start_review",
                       outcome="permission_denied", actor_role=Role.VIEWER)

    def test_invalid_transition_is_audited(self, client):
        _invoke(client, "kyc-1009", "approve", Role.SUPERVISOR)
        assert_audited("kyc_case", "kyc-1009", action="kyc.approve",
                       outcome="invalid_transition")

    def test_upstream_failure_is_audited(self, client, tool):
        tool.connector.fail_next(ErrKind.TIMEOUT)
        response = _invoke(client, "kyc-1004", "start_review", Role.OPERATOR)
        assert response.status_code == 502
        assert_audited("kyc_case", "kyc-1004", action="kyc.start_review",
                       outcome="upstream_failure")

    def test_audit_trail_visible_on_detail(self, client):
        _invoke(client, "kyc-1008", "start_review", Role.OPERATOR)
        detail = client.get("/api/kyc/resources/kyc-1008", headers=as_role(Role.VIEWER)).json()
        assert any(r["action"] == "kyc.start_review" and r["outcome"] == "success"
                   for r in detail["audit"])
