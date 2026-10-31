from abc import ABC, abstractmethod


class QuestionModel(ABC):
    @abstractmethod
    def read(self, text: str, metrics: list[str]) -> dict | None: ...


class LineRewriter(ABC):
    @abstractmethod
    def rewrite(self, line: str, tone: str) -> str | None: ...
