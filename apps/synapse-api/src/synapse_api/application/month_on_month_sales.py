from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.kpis import MonthSales
from synapse_api.domain.errors import InvalidQuery
from synapse_api.domain.gateways.sales_source import SalesSource


class GetMonthOnMonthSales:
    def __init__(self, source: SalesSource):
        self.source = source

    def execute(self, today: date, months: int = 12) -> list[MonthSales]:
        if not 1 <= months <= 24:
            raise InvalidQuery()
        first = today.year * 12 + today.month - 1 - (months - 1)
        start = date(first // 12, first % 12 + 1, 1)
        rows = self.source.daily_sales(start, today)
        currencies = sorted({r.currency for r in rows})
        totals: dict[tuple[str, int, int], Decimal] = {}
        for r in rows:
            key = (r.currency, r.date.year, r.date.month)
            totals[key] = totals.get(key, Decimal(0)) + r.net_amount
        result = []
        for index in range(first, first + months):
            year, month = index // 12, index % 12 + 1
            for currency in currencies:
                result.append(MonthSales(year, month, totals.get((currency, year, month), Decimal(0)), currency))
        return result
