"""SQLite persistence for platform concerns (audit log, idempotency keys).

App resource state lives in the (fake) system of record behind each app's connector,
not here. Tests use an in-memory database via ``use_memory_db``.
"""

import os
import sqlite3
import threading

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    error_kind TEXT,
    input_digest TEXT NOT NULL,
    before_state TEXT,
    after_state TEXT,
    detail TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log (resource_type, resource_id);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    outcome TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

_local = threading.local()
_memory_conn: sqlite3.Connection | None = None


def use_memory_db() -> None:
    """Switch to a fresh shared in-memory database (used by test fixtures)."""
    global _memory_conn
    _memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
    _memory_conn.row_factory = sqlite3.Row
    _memory_conn.executescript(_SCHEMA)


def use_file_db() -> None:
    global _memory_conn
    _memory_conn = None


def get_connection() -> sqlite3.Connection:
    if _memory_conn is not None:
        return _memory_conn
    conn = getattr(_local, "conn", None)
    if conn is None:
        path = os.environ.get("INTERNAL_TOOLS_DB", "data/internal-tools.db")
        if os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(_SCHEMA)
        _local.conn = conn
    return conn
