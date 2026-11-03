import sqlite3
from collections.abc import Callable

from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.where import column, where


class SqliteTable:
    def __init__(
        self,
        db: Database,
        source: str,
        to_entities: Callable[[list[sqlite3.Row]], list],
        scales: dict[str, int] | None = None,
        tie: str = "rowid ASC",
        source_params: list | None = None,
    ):
        self.db = db
        self.source = source
        self.tie = tie
        self.source_params = source_params or []
        self.to_entities = to_entities
        self.scales = scales or {}

    def fetch(self, condition, orderby: list[tuple[str, bool]], skip: int, top: int, count: bool, fields: dict) -> tuple[list, int | None]:
        clause, params = ("", []) if condition is None else (" WHERE " + (built := where(condition, self.scales))[0], built[1])
        order = "".join(f"{column(fields[name][0])} {'DESC' if descending else 'ASC'}, " for name, descending in orderby)
        rows = self.db.query(f"SELECT * FROM {self.source}{clause} ORDER BY {order}{self.tie} LIMIT ? OFFSET ?", [*self.source_params, *params, top, skip])
        total = self.db.query(f"SELECT COUNT(*) AS n FROM {self.source}{clause}", [*self.source_params, *params])[0]["n"] if count else None
        return self.to_entities(rows), total
