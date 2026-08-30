"""Append-only audit log. Every governed action outcome — including denials and
validation failures — is recorded here."""

import json
from datetime import datetime, timezone

from platform_core.db import get_connection
from pydantic import BaseModel


class AuditRecord(BaseModel):
    id: int
    ts: str
    actor_id: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: str
    outcome: str
    error_kind: str | None = None
    input_digest: str
    before_state: str | None = None
    after_state: str | None = None
    detail: dict | None = None


def record(
    *,
    actor_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: str,
    outcome: str,
    input_digest: str,
    error_kind: str | None = None,
    before_state: str | None = None,
    after_state: str | None = None,
    detail: dict | None = None,
) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO audit_log (ts, actor_id, actor_role, action, resource_type, resource_id,
           outcome, error_kind, input_digest, before_state, after_state, detail)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now(timezone.utc).isoformat(),
            actor_id,
            actor_role,
            action,
            resource_type,
            resource_id,
            outcome,
            error_kind,
            input_digest,
            before_state,
            after_state,
            json.dumps(detail) if detail is not None else None,
        ),
    )
    conn.commit()


def _row_to_record(row) -> AuditRecord:
    data = dict(row)
    data["detail"] = json.loads(data["detail"]) if data["detail"] else None
    return AuditRecord(**data)


def list_for_resource(resource_type: str, resource_id: str) -> list[AuditRecord]:
    rows = get_connection().execute(
        "SELECT * FROM audit_log WHERE resource_type = ? AND resource_id = ? ORDER BY id DESC",
        (resource_type, resource_id),
    ).fetchall()
    return [_row_to_record(r) for r in rows]


def list_recent(limit: int = 100) -> list[AuditRecord]:
    rows = get_connection().execute(
        "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [_row_to_record(r) for r in rows]
