from datetime import date, timedelta
from decimal import Decimal

from synapse_api.application.compare_metric import percent
from synapse_api.domain.entities.compare import MonthFigure, TrendMonth
from synapse_api.domain.entities.registry import Registry
from synapse_api.domain.errors import InvalidQuery, MetricNotFound
from synapse_api.domain.gateways.metric_source import MetricSource


def parse_month(text: str) -> date:
    try:
        return date.fromisoformat(f"{text}-01")
    except ValueError:
        raise InvalidQuery() from None


class GetMonthFigure:
    def __init__(self, source: MetricSource, registry: Registry):
        self.source = source
        self.registry = registry

    def execute(self, metric_name: str, today: date, month: str, trend: int = 6) -> list[MonthFigure]:
        metric = self.registry.metrics.get(metric_name)
        if metric is None:
            raise MetricNotFound()
        first = parse_month(month)
        if not 1 <= trend <= 24 or first > today.replace(day=1):
            raise InvalidQuery()
        end = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        index = first.year * 12 + first.month - 1
        start_index = index - trend
        start = date(start_index // 12, start_index % 12 + 1, 1)
        rows = self.source.rows(metric, "day", start, min(end, today))
        totals: dict[tuple[str, int], Decimal] = {}
        orders: dict[str, int] = {}
        for r in rows:
            key = (r.currency, r.date.year * 12 + r.date.month - 1)
            totals[key] = totals.get(key, Decimal(0)) + r.amount
            if (r.date.year, r.date.month) == (first.year, first.month):
                orders[r.currency] = orders.get(r.currency, 0) + (r.count or 0)
        figures = []
        for currency in sorted({r.currency for r in rows}):
            amount = totals.get((currency, index), Decimal(0))
            before = totals.get((currency, index - 1), Decimal(0))
            months = [
                TrendMonth(i // 12, i % 12 + 1, totals.get((currency, i), Decimal(0)))
                for i in range(index - trend + 1, index + 1)
            ]
            figures.append(MonthFigure(currency, amount, orders.get(currency, 0) if metric.dimensions["day"].count else None, percent(amount - before, before), end < today, months))
        return figures
