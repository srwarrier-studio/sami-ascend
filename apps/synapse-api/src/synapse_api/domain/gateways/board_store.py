from abc import ABC, abstractmethod

from synapse_api.domain.entities.board import Board, BoardWidget


class BoardStore(ABC):
    @abstractmethod
    def list_own(self, owner_id: str) -> list[Board]: ...

    @abstractmethod
    def list_public_of_others(self, owner_id: str) -> list[Board]: ...

    @abstractmethod
    def get(self, board_id: str) -> Board | None: ...

    @abstractmethod
    def add(self, board: Board) -> None: ...

    @abstractmethod
    def change(self, board_id: str, name: str, is_public: bool) -> None: ...

    @abstractmethod
    def set_widgets(self, board_id: str, widgets: list[BoardWidget]) -> None: ...

    @abstractmethod
    def delete(self, board_id: str) -> None: ...
