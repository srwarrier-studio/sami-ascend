from decimal import Decimal

from butterfly.domain.entities.sales_summary import SalesSummaryByCustomer
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


class SummarizeByCustomer:
    def __init__(self, repo: SalesOrderRepo):
        self.repo = repo

    def execute(self) -> list[SalesSummaryByCustomer]:
        totals: dict[tuple, list] = {}
        for order in self.repo.list_all():
            if order.overall_status == "X":
                continue
            key = (order.order_date, order.sold_to_party, order.transaction_currency, order.company_code)
            entry = totals.setdefault(key, [order.customer_name, Decimal("0.00"), 0, Decimal("0.00")])
            entry[1] += order.total_net_amount
            entry[2] += 1
            entry[3] += order.total_net_amount_local
        return [
            SalesSummaryByCustomer(party, name, day, amount, count, currency, company, local)
            for (day, party, currency, company), (name, amount, count, local) in sorted(totals.items())
        ]
