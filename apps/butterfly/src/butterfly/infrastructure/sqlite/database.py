import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager

from butterfly.infrastructure.sqlite.schema import TABLES

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
