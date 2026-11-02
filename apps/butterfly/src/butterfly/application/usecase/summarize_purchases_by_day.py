from decimal import Decimal

from butterfly.domain.entities.sales_summary import PurchaseSummaryByDay
from butterfly.domain.repositories.driver_repo import DriverRepo


class SummarizePurchasesByDay:
    def __init__(self, repo: DriverRepo):
        self.repo = repo

    def execute(self) -> list[PurchaseSummaryByDay]:
        totals: dict[tuple, list] = {}
        for delivery in self.repo.deliveries():
            if delivery.delivery_status == "X":
                continue
            entry = totals.setdefault((delivery.order_date, delivery.transaction_currency, delivery.company_code), [Decimal("0.00"), 0])
            entry[0] += delivery.net_amount
            entry[1] += 1
        return [PurchaseSummaryByDay(day, amount, count, currency, company) for (day, currency, company), (amount, count) in sorted(totals.items())]
