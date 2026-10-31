from decimal import Decimal

from butterfly.domain.entities.sales_summary import PurchaseSummaryByMaterial
from butterfly.domain.repositories.driver_repo import DriverRepo


class SummarizePurchasesByMaterial:
    def __init__(self, repo: DriverRepo):
        self.repo = repo

    def execute(self) -> list[PurchaseSummaryByMaterial]:
        totals: dict[tuple, list] = {}
        for delivery in self.repo.deliveries():
            if delivery.delivery_status == "X":
                continue
            key = (delivery.order_date, delivery.material, delivery.transaction_currency)
            entry = totals.setdefault(key, [delivery.material_description, delivery.quantity_unit, Decimal("0.000"), Decimal("0.00")])
            entry[2] += delivery.ordered_quantity
            entry[3] += delivery.net_amount
        return [
            PurchaseSummaryByMaterial(material, description, day, quantity, unit, amount, currency)
            for (day, material, currency), (description, unit, quantity, amount) in sorted(totals.items())
        ]
