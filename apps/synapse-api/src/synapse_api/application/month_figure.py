from datetime import date, timedelta
from decimal import Decimal

from synapse_api.application.compare_sales import percent
from synapse_api.domain.entities.compare import MonthFigure, TrendMonth
from synapse_api.domain.errors import InvalidQuery
from synapse_api.domain.gateways.sales_source import SalesSource


def parse_month(text: str) -> date:
    try:
        return date.fromisoformat(f"{text}-01")
    except ValueError:
        raise InvalidQuery() from None


class GetMonthFigure:
    def __init__(self, source: SalesSource):
        self.source = source

    def execute(self, today: date, month: str, trend: int = 6) -> list[MonthFigure]:
        first = parse_month(month)
        if not 1 <= trend <= 24 or first > today.replace(day=1):
            raise InvalidQuery()
        end = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        index = first.year * 12 + first.month - 1
        start_index = index - trend
        start = date(start_index // 12, start_index % 12 + 1, 1)
        rows = self.source.daily_sales(start, min(end, today))
        totals: dict[tuple[str, int], Decimal] = {}
        orders: dict[str, int] = {}
        for r in rows:
            key = (r.currency, r.date.year * 12 + r.date.month - 1)
            totals[key] = totals.get(key, Decimal(0)) + r.net_amount
            if (r.date.year, r.date.month) == (first.year, first.month):
                orders[r.currency] = orders.get(r.currency, 0) + r.order_count
        figures = []
        for currency in sorted({r.currency for r in rows}):
            amount = totals.get((currency, index), Decimal(0))
            before = totals.get((currency, index - 1), Decimal(0))
            months = [
                TrendMonth(i // 12, i % 12 + 1, totals.get((currency, i), Decimal(0)))
                for i in range(index - trend + 1, index + 1)
            ]
            figures.append(MonthFigure(currency, amount, orders.get(currency, 0), percent(amount - before, before), end < today, months))
        return figures
