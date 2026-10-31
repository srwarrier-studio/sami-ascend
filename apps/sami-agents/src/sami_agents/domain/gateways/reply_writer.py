from abc import ABC, abstractmethod


class ReplyWriter(ABC):
    @abstractmethod
    def write(self, message: str, titles: list[str], board_name: str | None) -> str: ...
