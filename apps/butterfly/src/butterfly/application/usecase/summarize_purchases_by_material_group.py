from decimal import Decimal

from butterfly.domain.entities.sales_summary import PurchaseSummaryByMaterialGroup
from butterfly.domain.repositories.driver_repo import DriverRepo


class SummarizePurchasesByMaterialGroup:
    def __init__(self, repo: DriverRepo, group_of: dict[str, str], names: dict[str, str]):
        self.repo = repo
        self.group_of = group_of
        self.names = names

    def execute(self) -> list[PurchaseSummaryByMaterialGroup]:
        totals: dict[tuple, list] = {}
        for delivery in self.repo.deliveries():
            group = self.group_of.get(delivery.material)
            if delivery.delivery_status == "X" or group is None:
                continue
            entry = totals.setdefault((delivery.order_date, group, delivery.transaction_currency, delivery.company_code), [Decimal("0.00"), 0])
            entry[0] += delivery.net_amount
            entry[1] += 1
        return [
            PurchaseSummaryByMaterialGroup(group, self.names.get(group), day, amount, count, currency, company)
            for (day, group, currency, company), (amount, count) in sorted(totals.items())
        ]
