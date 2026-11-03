import os
import sqlite3

from auth_api.domain.interface.auth_unit_of_work import AuthUnitOfWork
from auth_api.infrastructure.sqlite.sqlite_audit_repo import SqliteAuditRepo
from auth_api.infrastructure.sqlite.sqlite_user_repo import SqliteUserRepo

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    userid TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    fullname TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    disabled INTEGER NOT NULL,
    sap_username TEXT NOT NULL,
    entra_username TEXT,
    created_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS user_roles (
    userid TEXT NOT NULL REFERENCES users (userid),
    role TEXT NOT NULL,
    PRIMARY KEY (userid, role)
);
CREATE TABLE IF NOT EXISTS user_companies (
    userid TEXT NOT NULL REFERENCES users (userid),
    company TEXT NOT NULL,
    PRIMARY KEY (userid, company)
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    outcome TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT ''
);
"""

MIGRATIONS = [
    ("audit_log", "detail", "TEXT NOT NULL DEFAULT ''"),
    ("users", "entra_username", "TEXT"),
    ("users", "created_at", "TEXT NOT NULL DEFAULT ''"),
]


class SqliteAuthUnitOfWork(AuthUnitOfWork):
    def __init__(self, database_path: str):
        self.database_path = database_path
        conn = self._connect()
        conn.executescript(SCHEMA)
        for table, column, definition in MIGRATIONS:
            if column not in [info["name"] for info in conn.execute(f"PRAGMA table_info({table})")]:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_entra_username ON users (entra_username) WHERE entra_username IS NOT NULL")
        conn.commit()
        conn.close()
        os.chmod(database_path, 0o600)

    def __enter__(self):
        self.conn = self._connect()
        self.user_repo = SqliteUserRepo(self.conn)
        self.audit_repo = SqliteAuditRepo(self.conn)
        return self

    def __exit__(self, exc_type, exc, tb):
        super().__exit__(exc_type, exc, tb)
        self.conn.close()

    def rollback(self):
        self.conn.rollback()

    def commit(self):
        self.conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
