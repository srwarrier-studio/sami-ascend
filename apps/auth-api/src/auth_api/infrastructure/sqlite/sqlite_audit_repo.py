import sqlite3
from datetime import datetime

from auth_api.domain.entities.audit_event import AuditEvent
from auth_api.domain.repositories.audit_repo import AuditFilter, AuditRepo


class SqliteAuditRepo(AuditRepo):
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, event: AuditEvent) -> None:
        self.conn.execute(
            "INSERT INTO audit_log (at, actor, action, target, outcome, detail) VALUES (?, ?, ?, ?, ?, ?)",
            (event.at.isoformat(), event.actor, event.action, event.target, event.outcome, event.detail),
        )

    def list(self, filters: AuditFilter, limit: int, before: int | None) -> list[AuditEvent]:
        clauses, args = [], []
        for column, value in (("actor", filters.actor), ("action", filters.action), ("outcome", filters.outcome)):
            if value:
                clauses.append(f"{column} = ?")
                args.append(value)
        if filters.start:
            clauses.append("at >= ?")
            args.append(filters.start)
        if filters.end:
            clauses.append("at <= ?")
            args.append(filters.end)
        if before is not None:
            clauses.append("id < ?")
            args.append(before)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(
            f"SELECT id, at, actor, action, target, outcome, detail FROM audit_log {where} ORDER BY id DESC LIMIT ?", (*args, limit)
        ).fetchall()
        return [AuditEvent(r["actor"], r["action"], r["target"], r["outcome"], r["detail"], id=r["id"], at=datetime.fromisoformat(r["at"])) for r in rows]
