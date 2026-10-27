import sqlite3

from auth_api.domain.entities.audit_event import AuditEvent
from auth_api.domain.repositories.audit_repo import AuditRepo


class SqliteAuditRepo(AuditRepo):
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, event: AuditEvent) -> None:
        self.conn.execute(
            "INSERT INTO audit_log (at, actor, action, target, outcome) VALUES (?, ?, ?, ?, ?)",
            (event.at.isoformat(), event.actor, event.action, event.target, event.outcome),
        )
