"""Governed action pipeline — the single choke point for every mutation.

    authenticate -> authorize -> idempotency -> validate (state + input)
                 -> execute via connector -> audit the outcome
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from platform_core import audit
from platform_core.auth import Role, User
from platform_core.connectors import Command, CommandOutcome, Connector, Err, ErrKind
from platform_core.db import get_connection
from pydantic import BaseModel, ValidationError


class ActionError(Exception):
    outcome = "error"

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message


class PermissionDenied(ActionError):
    outcome = "permission_denied"


class InvalidTransition(ActionError):
    outcome = "invalid_transition"


class InvalidInput(ActionError):
    outcome = "invalid_input"


class ResourceNotFound(ActionError):
    outcome = "not_found"


class UpstreamFailure(ActionError):
    outcome = "upstream_failure"

    def __init__(self, kind: ErrKind, message: str = ""):
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class Action:
    """Declarative description of a governed mutation."""

    name: str  # e.g. "kyc.approve"
    command: str  # command name sent to the connector
    allowed_roles: frozenset[Role]
    valid_from_states: frozenset[str]
    to_state: str
    input_schema: type[BaseModel] | None = None
    payload_extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionResult:
    resource: dict
    new_state: str
    replayed: bool = False


def _digest(data: dict | None) -> str:
    return hashlib.sha256(json.dumps(data or {}, sort_keys=True).encode()).hexdigest()[:16]


def run_action(
    *,
    action: Action,
    actor: User,
    resource_id: str,
    connector: Connector,
    input_data: dict | None = None,
    idempotency_key: str,
) -> ActionResult:
    """Execute ``action`` as ``actor`` on ``resource_id`` through ``connector``.

    Raises an ``ActionError`` subclass on any failure. Every outcome, success or
    failure, is written to the audit log.
    """
    digest = _digest(input_data)

    def audited(outcome: str, *, error_kind: str | None = None, before: str | None = None,
                after: str | None = None, detail: dict | None = None) -> None:
        audit.record(
            actor_id=actor.id,
            actor_role=actor.role.value,
            action=action.name,
            resource_type=connector.resource_type,
            resource_id=resource_id,
            outcome=outcome,
            error_kind=error_kind,
            input_digest=digest,
            before_state=before,
            after_state=after,
            detail=detail,
        )

    # 1-2. authenticate (actor is resolved upstream) + authorize
    if actor.role not in action.allowed_roles:
        audited(PermissionDenied.outcome)
        raise PermissionDenied(f"Role {actor.role.value} may not perform {action.name}")

    # 3. idempotency — a replayed request returns the recorded outcome without
    # re-executing (checked before state validation: the first execution already
    # moved the resource on, so re-validating would wrongly report InvalidTransition)
    conn = get_connection()
    row = conn.execute(
        "SELECT action, outcome FROM idempotency_keys WHERE key = ?", (idempotency_key,)
    ).fetchone()
    if row is not None:
        if row["action"] != action.name:
            audited(InvalidInput.outcome)
            raise InvalidInput("Idempotency key was already used for a different action")
        recorded = json.loads(row["outcome"])
        return ActionResult(resource=recorded["resource"], new_state=recorded["new_state"],
                            replayed=True)

    # 4a. validate current state
    current = connector.get(resource_id)
    if isinstance(current, Err):
        if current.kind == ErrKind.NOT_FOUND:
            audited(ResourceNotFound.outcome, error_kind=current.kind.value)
            raise ResourceNotFound(current.message)
        audited(UpstreamFailure.outcome, error_kind=current.kind.value)
        raise UpstreamFailure(current.kind, current.message)
    before_state = current.value.get("state")
    if before_state not in action.valid_from_states:
        audited(InvalidTransition.outcome, before=before_state)
        raise InvalidTransition(
            f"{action.name} not allowed from state {before_state!r}"
        )

    # 4b. validate input
    payload: dict[str, Any] = dict(action.payload_extra)
    if action.input_schema is not None:
        try:
            payload.update(action.input_schema(**(input_data or {})).model_dump())
        except ValidationError as exc:
            audited(InvalidInput.outcome, before=before_state,
                    detail={"errors": json.loads(exc.json())})
            raise InvalidInput(str(exc)) from exc

    # 5. execute through the connector
    payload["actor_id"] = actor.id
    result = connector.execute(
        Command(name=action.command, resource_id=resource_id, payload=payload),
        idempotency_key,
    )
    if isinstance(result, Err):
        audited(UpstreamFailure.outcome, error_kind=result.kind.value, before=before_state)
        raise UpstreamFailure(result.kind, result.message)
    outcome: CommandOutcome = result.value

    conn.execute(
        "INSERT INTO idempotency_keys (key, action, outcome, created_at) VALUES (?, ?, ?, ?)",
        (
            idempotency_key,
            action.name,
            json.dumps({"resource": outcome.resource, "new_state": outcome.new_state}),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()

    # 6. audit the success
    audited("success", before=before_state, after=outcome.new_state)
    return ActionResult(resource=outcome.resource, new_state=outcome.new_state)


def authorize_read(actor: User, allowed_roles: frozenset[Role]) -> None:
    if actor.role not in allowed_roles:
        raise PermissionDenied(f"Role {actor.role.value} may not read this resource")


ALL_ROLES = frozenset({Role.VIEWER, Role.OPERATOR, Role.SUPERVISOR})


def actions_available(actions: list[Action], actor: User, state: str) -> list[str]:
    """Names of actions the actor may perform on a resource in ``state`` (drives the UI)."""
    return [
        a.name
        for a in actions
        if actor.role in a.allowed_roles and state in a.valid_from_states
    ]


HandlerMap = dict[str, Callable[..., Any]]
