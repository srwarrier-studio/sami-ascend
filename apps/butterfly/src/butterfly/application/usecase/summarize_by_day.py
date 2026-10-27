from decimal import Decimal

from butterfly.domain.entities.sales_summary import SalesSummaryByDay
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


class SummarizeByDay:
    def __init__(self, repo: SalesOrderRepo):
        self.repo = repo

    def execute(self) -> list[SalesSummaryByDay]:
        totals: dict[tuple, tuple[Decimal, int]] = {}
        for order in self.repo.list_all():
            if order.overall_status == "X":
                continue
            key = (order.order_date, order.transaction_currency)
            amount, count = totals.get(key, (Decimal("0.00"), 0))
            totals[key] = (amount + order.total_net_amount, count + 1)
        return [
            SalesSummaryByDay(day, amount, count, currency)
            for (day, currency), (amount, count) in sorted(totals.items())
        ]
