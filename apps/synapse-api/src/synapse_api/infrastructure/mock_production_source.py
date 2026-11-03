from datetime import date

from synapse_api.domain.entities.production import DowntimeDay, LineShiftOutput, OpenOrder, ProductionDay, ScrapDay
from synapse_api.domain.gateways.production_source import ProductionSource


class MockProductionSource(ProductionSource):
    def __init__(
        self,
        days: list[ProductionDay] | None = None,
        downtimes: list[DowntimeDay] | None = None,
        scraps: list[ScrapDay] | None = None,
        lines: list[LineShiftOutput] | None = None,
        orders: list[OpenOrder] | None = None,
    ):
        self.days = days or []
        self.downtimes = downtimes or []
        self.scraps = scraps or []
        self.lines = lines or []
        self.orders = orders or []

    def for_companies(self, companies: tuple[str, ...]) -> "MockProductionSource":
        return self

    def day_summaries(self, start: date, end: date) -> list[ProductionDay]:
        return [row for row in self.days if start <= row.day <= end]

    def downtime_summaries(self, start: date, end: date) -> list[DowntimeDay]:
        return [row for row in self.downtimes if start <= row.day <= end]

    def scrap_summaries(self, start: date, end: date) -> list[ScrapDay]:
        return [row for row in self.scraps if start <= row.day <= end]

    def line_shift_output(self, start: date, end: date) -> list[LineShiftOutput]:
        return [row for row in self.lines if start <= row.day <= end]

    def open_orders(self, top: int) -> list[OpenOrder]:
        return sorted(self.orders, key=lambda order: (order.start, order.order))[:top]
