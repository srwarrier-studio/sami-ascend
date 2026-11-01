from abc import ABC, abstractmethod

from intent_api.domain.entities.match import Match


class UnansweredLog(ABC):
    @abstractmethod
    def record(self, question: str, match: Match) -> None: ...

    @abstractmethod
    def entries(self) -> list[dict]: ...
