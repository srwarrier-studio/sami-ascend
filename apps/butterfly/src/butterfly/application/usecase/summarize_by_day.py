from decimal import Decimal

from butterfly.domain.entities.sales_summary import SalesSummaryByDay
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


class SummarizeByDay:
    def __init__(self, repo: SalesOrderRepo):
        self.repo = repo

    def execute(self) -> list[SalesSummaryByDay]:
        totals: dict[tuple, tuple[Decimal, int, Decimal]] = {}
        for order in self.repo.list_all():
            if order.overall_status == "X":
                continue
            key = (order.order_date, order.transaction_currency, order.company_code)
            amount, count, local = totals.get(key, (Decimal("0.00"), 0, Decimal("0.00")))
            totals[key] = (amount + order.total_net_amount, count + 1, local + order.total_net_amount_local)
        return [
            SalesSummaryByDay(day, amount, count, currency, company, local)
            for (day, currency, company), (amount, count, local) in sorted(totals.items())
        ]
