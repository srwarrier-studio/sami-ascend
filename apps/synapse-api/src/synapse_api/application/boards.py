from collections.abc import Callable
from uuid import uuid4

from synapse_api.domain.entities.board import Board, BoardWidget
from synapse_api.domain.errors import BoardLimit, BoardNotFound, BoardNotOwned, WidgetNotAllowed
from synapse_api.domain.gateways.board_store import BoardStore

MAX_BOARDS = 3


class Boards:
    def __init__(self, store: BoardStore, can_see: Callable[[str], bool]):
        self.store = store
        self.can_see = can_see

    def visible(self, board: Board) -> Board:
        return Board(board.id, board.owner_id, board.owner_name, board.name, board.is_public, [w for w in board.widgets if self.can_see(w.catalog_id)])

    def checked(self, widgets: list[BoardWidget]) -> list[BoardWidget]:
        for widget in widgets:
            if not self.can_see(widget.catalog_id):
                raise WidgetNotAllowed(widget.catalog_id)
        return widgets

    def owned(self, board_id: str, owner_id: str) -> Board:
        board = self.store.get(board_id)
        if board is None or (board.owner_id != owner_id and not board.is_public):
            raise BoardNotFound(board_id)
        if board.owner_id != owner_id:
            raise BoardNotOwned(board_id)
        return board

    def mine(self, owner_id: str) -> list[Board]:
        return [self.visible(board) for board in self.store.list_own(owner_id)]

    def create(self, owner_id: str, owner_name: str, name: str, is_public: bool, widgets: list[BoardWidget]) -> Board:
        if len(self.store.list_own(owner_id)) >= MAX_BOARDS:
            raise BoardLimit(owner_id)
        board = Board(uuid4().hex, owner_id, owner_name, name, is_public, self.checked(widgets))
        self.store.add(board)
        return board

    def change(self, board_id: str, owner_id: str, name: str | None, is_public: bool | None) -> Board:
        board = self.owned(board_id, owner_id)
        self.store.change(board_id, board.name if name is None else name, board.is_public if is_public is None else is_public)
        return self.visible(self.store.get(board_id))

    def save_widgets(self, board_id: str, owner_id: str, widgets: list[BoardWidget]) -> Board:
        board = self.owned(board_id, owner_id)
        hidden = [w for w in board.widgets if not self.can_see(w.catalog_id)]
        self.store.set_widgets(board_id, self.checked(widgets) + hidden)
        return self.visible(self.store.get(board_id))

    def delete(self, board_id: str, owner_id: str) -> None:
        self.owned(board_id, owner_id)
        self.store.delete(board_id)

    def shared(self, viewer_id: str) -> list[Board]:
        seen = (self.visible(board) for board in self.store.list_public_of_others(viewer_id))
        return [board for board in seen if board.widgets]

    def copy_shared(self, board_id: str, viewer_id: str, viewer_name: str) -> Board:
        source = self.store.get(board_id)
        if source is None or not source.is_public or source.owner_id == viewer_id:
            raise BoardNotFound(board_id)
        widgets = self.visible(source).widgets
        if not widgets:
            raise BoardNotFound(board_id)
        return self.create(viewer_id, viewer_name, source.name, False, widgets)
