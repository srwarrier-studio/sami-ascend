from datetime import date

from synapse_api.domain.entities.metric_row import MetricRow
from synapse_api.domain.entities.registry import Metric
from synapse_api.domain.errors import SapUnavailable
from synapse_api.domain.gateways.metric_source import MetricSource


class MockMetricSource(MetricSource):
    def __init__(self, rows: dict[tuple[str, str], list[MetricRow]] | None = None):
        self.stored = rows or {}
        self.failing = False
        self.calls = 0

    def fail(self) -> None:
        self.failing = True

    def rows(self, metric: Metric, dimension: str, start: date, end: date) -> list[MetricRow]:
        self.calls += 1
        if self.failing:
            raise SapUnavailable()
        rows = self.stored.get((metric.name, dimension), [])
        return sorted((r for r in rows if start <= r.date <= end), key=lambda r: r.date)
