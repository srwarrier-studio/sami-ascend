from abc import ABC, abstractmethod
from datetime import date

from intent_api.domain.entities.figures import Comparison, MonthFigure, Window


class MetricSource(ABC):
    @abstractmethod
    def month(self, token: str, metric: str, month: date, trend: int) -> list[MonthFigure]: ...

    @abstractmethod
    def compare(self, token: str, metric: str, window: Window, by: str | None, top: int) -> list[Comparison]: ...
