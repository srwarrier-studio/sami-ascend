from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.kpis import SalesTotal
from synapse_api.domain.gateways.sales_source import SalesSource


def total_per_currency(source: SalesSource, start: date, end: date) -> list[SalesTotal]:
    amounts: dict[str, Decimal] = {}
    counts: dict[str, int] = {}
    for row in source.daily_sales(start, end):
        amounts[row.currency] = amounts.get(row.currency, Decimal(0)) + row.net_amount
        counts[row.currency] = counts.get(row.currency, 0) + row.order_count
    return [SalesTotal(start, end, amounts[c], counts[c], c) for c in sorted(amounts)]


class GetTodaySales:
    def __init__(self, source: SalesSource):
        self.source = source

    def execute(self, today: date) -> list[SalesTotal]:
        return total_per_currency(self.source, today, today)


class GetMonthToDateSales:
    def __init__(self, source: SalesSource):
        self.source = source

    def execute(self, today: date) -> list[SalesTotal]:
        return total_per_currency(self.source, today.replace(day=1), today)


class GetYearToDateSales:
    def __init__(self, source: SalesSource):
        self.source = source

    def execute(self, today: date) -> list[SalesTotal]:
        return total_per_currency(self.source, today.replace(month=1, day=1), today)
