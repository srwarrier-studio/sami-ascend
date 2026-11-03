import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager

from butterfly.infrastructure.sqlite.schema import ADDED_COLUMNS, BACKFILL, TABLES
from butterfly.infrastructure.sqlite.views import view_script

MEMORY = ":memory:"


class Database:
    def __init__(self, path: str = MEMORY):
        self.path = path
        self.lock = threading.RLock()
        self.connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        if path != MEMORY:
            self.connection.execute("PRAGMA journal_mode=WAL")
        with self.lock:
            self.connection.executescript(TABLES)
            self.add_missing_columns()
            self.connection.executescript(view_script())

    def add_missing_columns(self) -> None:
        for table, column, definition in ADDED_COLUMNS:
            if column not in {row["name"] for row in self.connection.execute(f"PRAGMA table_info({table})")}:
                self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        for statement in BACKFILL:
            self.connection.execute(statement)

    def query(self, sql: str, params: tuple | list = ()) -> list[sqlite3.Row]:
        with self.lock:
            return self.connection.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple | list = ()) -> None:
        with self.lock:
            self.connection.execute(sql, params)

    def insert_many(self, sql: str, rows: list[tuple]) -> None:
        with self.lock:
            self.connection.executemany(sql, rows)

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self.lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                yield
            except BaseException:
                self.connection.execute("ROLLBACK")
                raise
            self.connection.execute("COMMIT")

    def close(self) -> None:
        with self.lock:
            self.connection.close()
