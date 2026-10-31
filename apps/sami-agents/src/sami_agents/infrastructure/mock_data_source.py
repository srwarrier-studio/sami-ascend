from datetime import date

from sami_agents.domain.entities.finding import MemberChange, Window
from sami_agents.domain.entities.measure import Comparison, MetricInfo, TrendPoint
from sami_agents.domain.errors import DataUnavailable
from sami_agents.domain.gateways.data_source import DataSource


class MockDataSource(DataSource):
    def __init__(
        self,
        records: dict[str, list[dict]] | None = None,
        changes: dict[tuple[str, str, str], MemberChange] | None = None,
        infos: list[MetricInfo] | None = None,
        comparisons: dict[tuple[str, str | None], list[Comparison]] | None = None,
        trends: dict[str, list[TrendPoint]] | None = None,
    ):
        self.stored = records or {}
        self.changes = changes or {}
        self.infos = infos or []
        self.comparisons = comparisons or {}
        self.trends = trends or {}
        self.calls: list[tuple] = []
        self.tokens: list[str] = []
        self.failing = False

    def fail(self) -> None:
        self.failing = True

    def records(self, token: str, record_type: str, key_field: str, key: str, start: date | None, end: date | None) -> list[dict]:
        self.note(token, ("records", record_type, key_field, key, start, end))
        return [row for row in self.stored.get(record_type, []) if row.get(key_field) == key]

    def member_change(self, token: str, metric: str, dimension: str, key: str, window: Window) -> MemberChange | None:
        self.note(token, ("member_change", metric, dimension, key, window))
        return self.changes.get((metric, dimension, key))

    def metrics(self, token: str) -> list[MetricInfo]:
        self.note(token, ("metrics",))
        return self.infos

    def compare(self, token: str, metric: str, window: Window, by: str | None, top: int) -> list[Comparison]:
        self.note(token, ("compare", metric, by, window))
        return self.comparisons.get((metric, by), [])

    def trend(self, token: str, metric: str, month: date, months: int) -> list[TrendPoint]:
        self.note(token, ("trend", metric, month, months))
        return self.trends.get(metric, [])

    def note(self, token: str, call: tuple) -> None:
        self.tokens.append(token)
        self.calls.append(call)
        if self.failing:
            raise DataUnavailable("mock is failing")
