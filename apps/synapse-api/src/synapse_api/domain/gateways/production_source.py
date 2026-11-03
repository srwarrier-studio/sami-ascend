from abc import ABC, abstractmethod
from datetime import date

from synapse_api.domain.entities.production import DowntimeDay, LineShiftOutput, OpenOrder, ProductionDay, ScrapDay


class ProductionSource(ABC):
    @abstractmethod
    def for_companies(self, companies: tuple[str, ...]) -> "ProductionSource": ...

    @abstractmethod
    def day_summaries(self, start: date, end: date) -> list[ProductionDay]: ...

    @abstractmethod
    def downtime_summaries(self, start: date, end: date) -> list[DowntimeDay]: ...

    @abstractmethod
    def scrap_summaries(self, start: date, end: date) -> list[ScrapDay]: ...

    @abstractmethod
    def line_shift_output(self, start: date, end: date) -> list[LineShiftOutput]: ...

    @abstractmethod
    def open_orders(self, top: int) -> list[OpenOrder]: ...
