from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class FoundDate:
    text: str
    grain: str
    day: date


class FallbackPeriods(ABC):
    @abstractmethod
    def find(self, text: str, today: date) -> list[FoundDate]: ...
