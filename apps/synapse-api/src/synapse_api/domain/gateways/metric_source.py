from abc import ABC, abstractmethod
from datetime import date

from synapse_api.domain.entities.metric_row import MetricRow
from synapse_api.domain.entities.registry import Metric


class MetricSource(ABC):
    @abstractmethod
    def for_companies(self, companies: tuple[str, ...]) -> "MetricSource": ...

    @abstractmethod
    def rows(self, metric: Metric, dimension: str, start: date, end: date) -> list[MetricRow]: ...
