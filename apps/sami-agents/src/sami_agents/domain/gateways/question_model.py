from abc import ABC, abstractmethod


class QuestionModel(ABC):
    @abstractmethod
    def read(self, text: str, metrics: list[str]) -> dict | None: ...


class HeadlineRewriter(ABC):
    @abstractmethod
    def rewrite(self, headline: str) -> str | None: ...
