import json
import sqlite3
import threading

from synapse_api.domain.entities.board import Board, BoardWidget
from synapse_api.domain.gateways.board_store import BoardStore

COLUMNS = "id, owner_id, owner_name, name, is_public, widgets"


def board_from(row: tuple) -> Board:
    id_, owner_id, owner_name, name, is_public, widgets = row
    return Board(id_, owner_id, owner_name, name, bool(is_public), [BoardWidget(**widget) for widget in json.loads(widgets)])


def widgets_text(widgets: list[BoardWidget]) -> str:
    return json.dumps([{"id": w.id, "catalog_id": w.catalog_id, "size": w.size} for w in widgets])


class SqliteBoardStore(BoardStore):
    def __init__(self, path: str):
        self.lock = threading.Lock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.run(
            "CREATE TABLE IF NOT EXISTS boards (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, owner_name TEXT NOT NULL,"
            " name TEXT NOT NULL, is_public INTEGER NOT NULL, widgets TEXT NOT NULL,"
            " created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )

    def run(self, sql: str, args: tuple = ()) -> list[tuple]:
        with self.lock, self.db:
            return self.db.execute(sql, args).fetchall()

    def list_own(self, owner_id: str) -> list[Board]:
        return [board_from(row) for row in self.run(f"SELECT {COLUMNS} FROM boards WHERE owner_id = ? ORDER BY created_at, rowid", (owner_id,))]

    def list_public_of_others(self, owner_id: str) -> list[Board]:
        return [board_from(row) for row in self.run(f"SELECT {COLUMNS} FROM boards WHERE owner_id != ? AND is_public = 1 ORDER BY updated_at DESC, rowid", (owner_id,))]

    def get(self, board_id: str) -> Board | None:
        rows = self.run(f"SELECT {COLUMNS} FROM boards WHERE id = ?", (board_id,))
        return board_from(rows[0]) if rows else None

    def add(self, board: Board) -> None:
        self.run(f"INSERT INTO boards ({COLUMNS}) VALUES (?,?,?,?,?,?)", (board.id, board.owner_id, board.owner_name, board.name, int(board.is_public), widgets_text(board.widgets)))

    def change(self, board_id: str, name: str, is_public: bool) -> None:
        self.run("UPDATE boards SET name = ?, is_public = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (name, int(is_public), board_id))

    def set_widgets(self, board_id: str, widgets: list[BoardWidget]) -> None:
        self.run("UPDATE boards SET widgets = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (widgets_text(widgets), board_id))

    def delete(self, board_id: str) -> None:
        self.run("DELETE FROM boards WHERE id = ?", (board_id,))
