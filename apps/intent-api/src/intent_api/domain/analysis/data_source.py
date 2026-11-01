from abc import ABC, abstractmethod
from datetime import date

from intent_api.domain.analysis.finding import MemberChange, Window
from intent_api.domain.analysis.measure import Comparison, MetricInfo, TrendPoint


class DataSource(ABC):
    @abstractmethod
    def for_company(self, company: str | None) -> "DataSource": ...

    @abstractmethod
    def records(self, token: str, record_type: str, key_field: str, key: str, start: date | None, end: date | None) -> list[dict]: ...

    @abstractmethod
    def member_change(self, token: str, metric: str, dimension: str, key: str, window: Window) -> MemberChange | None: ...

    @abstractmethod
    def metrics(self, token: str) -> list[MetricInfo]: ...

    @abstractmethod
    def compare(self, token: str, metric: str, window: Window, by: str | None, top: int) -> list[Comparison]: ...

    @abstractmethod
    def trend(self, token: str, metric: str, month: date, months: int) -> list[TrendPoint]: ...
