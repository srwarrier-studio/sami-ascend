from abc import ABC, abstractmethod


class PairScorer(ABC):
    @abstractmethod
    def logits(self, question: str, options: list[str]) -> list[float]: ...
