from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.metric_row import MetricRow
from synapse_api.domain.entities.registry import Dimension, Metric
from synapse_api.domain.gateways.metric_source import MetricSource
from synapse_api.infrastructure.odata_reader import ODataReader


class RegistryMetricSource(MetricSource):
    def __init__(self, readers: dict[str, ODataReader]):
        self.readers = readers

    def rows(self, metric: Metric, dimension: str, start: date, end: date) -> list[MetricRow]:
        spec = metric.dimensions[dimension]
        filter_ = f"{metric.date}%20ge%20{start.isoformat()}%20and%20{metric.date}%20le%20{end.isoformat()}"
        path = f"{spec.entity}?$filter={filter_}&$orderby={spec.order}"
        return [self.to_row(metric, spec, row) for row in self.readers[metric.service].all_rows(path)]

    def to_row(self, metric: Metric, spec: Dimension, row: dict) -> MetricRow:
        return MetricRow(
            row[spec.key] if spec.key else None,
            (row[spec.name_field] or "") if spec.name_field else "",
            date.fromisoformat(row[metric.date]),
            Decimal(row[metric.measure]),
            row[metric.currency],
            Decimal(row[spec.quantity]) if spec.quantity else None,
            row[spec.unit] if spec.unit else None,
            row[spec.count] if spec.count else None,
        )
