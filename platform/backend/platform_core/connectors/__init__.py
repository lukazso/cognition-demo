"""Typed connector contract — the only way app code touches a system of record.

Every call returns ``Ok | Err`` with a fixed error taxonomy; no connector-specific
exceptions leak upward. Commands carry idempotency keys end to end.
``FakeConnector`` is the scriptable in-memory implementation used by the POC runtime
and by tests (supports failure injection via ``fail_next``).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, Protocol, TypeVar

T = TypeVar("T")


class ErrKind(str, Enum):
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    UPSTREAM_ERROR = "upstream_error"
    INVALID_REQUEST = "invalid_request"


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True)
class Err:
    kind: ErrKind
    message: str = ""


ConnectorResult = Ok[T] | Err


@dataclass(frozen=True)
class Query:
    filters: dict[str, str] = field(default_factory=dict)
    search: str | None = None
    page: int = 1
    page_size: int = 50


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    total: int


@dataclass(frozen=True)
class Command:
    name: str
    resource_id: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandOutcome:
    resource: dict[str, Any]
    new_state: str | None = None  # None for resources without a lifecycle
    resource_id: str | None = None  # id assigned by the system of record on creation


class Connector(Protocol):
    resource_type: str

    def list(self, query: Query) -> ConnectorResult[Page[dict]]: ...
    def get(self, resource_id: str) -> ConnectorResult[dict]: ...
    def execute(self, command: Command, idempotency_key: str) -> ConnectorResult[CommandOutcome]: ...
    # Creation is separate: there is no resource to fetch yet, and the system of
    # record assigns the id, returned as ``CommandOutcome.resource_id``.
    def create(self, command: Command, idempotency_key: str) -> ConnectorResult[CommandOutcome]: ...


class FakeConnector:
    """In-memory system of record.

    Subclasses set ``resource_type``, seed ``self.records`` (id -> dict; include a
    ``state`` key only if the resource has a lifecycle), and implement
    ``apply_command`` to mutate a record for a given command. Subclasses that support
    creation also implement ``build_record``.
    """

    resource_type = "resource"
    id_field = "id"

    def __init__(self) -> None:
        self.records: dict[str, dict] = {}
        self._fail_next: Err | None = None
        self._seen_keys: dict[str, CommandOutcome] = {}

    # -- test/demo helpers -------------------------------------------------
    def fail_next(self, kind: ErrKind, message: str = "injected failure") -> None:
        self._fail_next = Err(kind=kind, message=message)

    def _pop_injected_failure(self) -> Err | None:
        err, self._fail_next = self._fail_next, None
        return err

    # -- contract ----------------------------------------------------------
    def list(self, query: Query) -> ConnectorResult[Page[dict]]:
        if (err := self._pop_injected_failure()) is not None:
            return err
        items = list(self.records.values())
        for key, value in query.filters.items():
            items = [r for r in items if str(r.get(key)) == value]
        if query.search:
            needle = query.search.lower()
            items = [r for r in items if needle in str(r).lower()]
        total = len(items)
        start = (query.page - 1) * query.page_size
        return Ok(Page(items=items[start : start + query.page_size], total=total))

    def get(self, resource_id: str) -> ConnectorResult[dict]:
        if (err := self._pop_injected_failure()) is not None:
            return err
        record = self.records.get(resource_id)
        if record is None:
            return Err(kind=ErrKind.NOT_FOUND, message=f"{self.resource_type} {resource_id}")
        return Ok(record)

    def execute(self, command: Command, idempotency_key: str) -> ConnectorResult[CommandOutcome]:
        if idempotency_key in self._seen_keys:
            return Ok(self._seen_keys[idempotency_key])
        if (err := self._pop_injected_failure()) is not None:
            return err
        record = self.records.get(command.resource_id)
        if record is None:
            return Err(kind=ErrKind.NOT_FOUND, message=f"{self.resource_type} {command.resource_id}")
        result = self.apply_command(record, command)
        if isinstance(result, Err):
            return result
        outcome = CommandOutcome(
            resource=dict(record), new_state=record.get("state"), resource_id=command.resource_id
        )
        self._seen_keys[idempotency_key] = outcome
        return Ok(outcome)

    def create(self, command: Command, idempotency_key: str) -> ConnectorResult[CommandOutcome]:
        if idempotency_key in self._seen_keys:
            return Ok(self._seen_keys[idempotency_key])
        if (err := self._pop_injected_failure()) is not None:
            return err
        result = self.build_record(command)
        if isinstance(result, Err):
            return result
        resource_id = str(result[self.id_field])
        if resource_id in self.records:
            return Err(kind=ErrKind.CONFLICT, message=f"{self.resource_type} {resource_id} exists")
        self.records[resource_id] = result
        outcome = CommandOutcome(
            resource=dict(result), new_state=result.get("state"), resource_id=resource_id
        )
        self._seen_keys[idempotency_key] = outcome
        return Ok(outcome)

    def apply_command(self, record: dict, command: Command) -> Err | None:
        raise NotImplementedError

    def build_record(self, command: Command) -> dict | Err:
        """Build the new record (including its ``id_field``) for a creating command, or
        return ``Err`` when the system of record rejects it (e.g. a duplicate key)."""
        raise NotImplementedError
