from decimal import Decimal

from butterfly.domain.entities.sales_summary import PurchaseSummaryBySupplier
from butterfly.domain.repositories.driver_repo import DriverRepo


class SummarizePurchasesBySupplier:
    def __init__(self, repo: DriverRepo):
        self.repo = repo

    def execute(self) -> list[PurchaseSummaryBySupplier]:
        totals: dict[tuple, list] = {}
        for delivery in self.repo.deliveries():
            if delivery.delivery_status == "X":
                continue
            key = (delivery.order_date, delivery.supplier, delivery.transaction_currency)
            entry = totals.setdefault(key, [delivery.supplier_name, Decimal("0.00"), 0])
            entry[1] += delivery.net_amount
            entry[2] += 1
        return [
            PurchaseSummaryBySupplier(supplier, name, day, amount, count, currency)
            for (day, supplier, currency), (name, amount, count) in sorted(totals.items())
        ]
