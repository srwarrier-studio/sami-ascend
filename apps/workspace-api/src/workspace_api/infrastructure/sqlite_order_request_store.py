import json
import sqlite3
import threading
from datetime import datetime, timezone

from workspace_api.domain.entities.order_request import OPEN, QUEUED, SENDING, UNKNOWN, OrderRequest
from workspace_api.domain.errors import StoreUnavailable
from workspace_api.domain.repositories.order_request_store import OrderRequestStore

COLUMNS = "id, user, sap_username, request_id, body, status, attempts, next_attempt_at, created_at, updated_at, sales_order, details, message"
CHANGEABLE = {"status", "attempts", "next_attempt_at", "sales_order", "details", "message"}


def text_of(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def request_from(row: tuple) -> OrderRequest:
    id_, user, sap_username, request_id, body, status, attempts, next_at, created, updated, sales_order, details, message = row
    return OrderRequest(
        id_, user, sap_username, request_id, json.loads(body), status, attempts,
        datetime.fromisoformat(next_at), datetime.fromisoformat(created), datetime.fromisoformat(updated),
        sales_order, json.loads(details) if details else None, message,
    )


class SqliteOrderRequestStore(OrderRequestStore):
    def __init__(self, path: str, clock=lambda: datetime.now(timezone.utc)):
        self.clock = clock
        self.lock = threading.Lock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.run(
            "CREATE TABLE IF NOT EXISTS order_requests (id TEXT PRIMARY KEY, user TEXT NOT NULL, sap_username TEXT NOT NULL,"
            " request_id TEXT, body TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL, next_attempt_at TEXT NOT NULL,"
            " created_at TEXT NOT NULL, updated_at TEXT NOT NULL, sales_order TEXT, details TEXT, message TEXT)"
        )

    def run(self, sql: str, args: tuple = ()) -> list[tuple]:
        try:
            with self.lock, self.db:
                return self.db.execute(sql, args).fetchall()
        except sqlite3.Error as error:
            raise StoreUnavailable(type(error).__name__) from error

    def add(self, request: OrderRequest) -> None:
        self.run(
            f"INSERT INTO order_requests ({COLUMNS}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (request.id, request.user, request.sap_username, request.request_id, json.dumps(request.body), request.status, request.attempts,
             text_of(request.next_attempt_at), text_of(request.created_at), text_of(request.updated_at), request.sales_order,
             json.dumps(request.details) if request.details is not None else None, request.message),
        )

    def claim_due(self, now: datetime) -> OrderRequest | None:
        try:
            with self.lock, self.db:
                row = self.db.execute(
                    f"SELECT {COLUMNS} FROM order_requests WHERE status = ? AND next_attempt_at <= ? ORDER BY created_at, id LIMIT 1",
                    (QUEUED, text_of(now)),
                ).fetchone()
                if row is None:
                    return None
                self.db.execute("UPDATE order_requests SET status = ?, updated_at = ? WHERE id = ?", (SENDING, text_of(self.clock()), row[0]))
        except sqlite3.Error as error:
            raise StoreUnavailable(type(error).__name__) from error
        return request_from((*row[:5], SENDING, *row[6:]))

    def update(self, request_id: str, **changes) -> None:
        assert set(changes) <= CHANGEABLE, changes
        values = {k: (text_of(v) if isinstance(v, datetime) else json.dumps(v) if k == "details" and v is not None else v) for k, v in changes.items()}
        values["updated_at"] = text_of(self.clock())
        sets = ", ".join(f"{name} = ?" for name in values)
        self.run(f"UPDATE order_requests SET {sets} WHERE id = ?", (*values.values(), request_id))

    def recover_sending(self) -> int:
        stuck = self.run("SELECT id FROM order_requests WHERE status = ?", (SENDING,))
        for (request_id,) in stuck:
            self.update(request_id, status=UNKNOWN, message="The app stopped while sending this order; check SAP before entering it again.")
        return len(stuck)

    def get(self, request_id: str, user: str) -> OrderRequest | None:
        rows = self.run(f"SELECT {COLUMNS} FROM order_requests WHERE id = ? AND user = ?", (request_id, user))
        return request_from(rows[0]) if rows else None

    def list_open(self, user: str, limit: int) -> list[OrderRequest]:
        marks = ",".join("?" * len(OPEN))
        rows = self.run(
            f"SELECT {COLUMNS} FROM order_requests WHERE user = ? AND status IN ({marks}) ORDER BY created_at DESC, id DESC LIMIT ?",
            (user, *OPEN, limit),
        )
        return [request_from(row) for row in rows]
