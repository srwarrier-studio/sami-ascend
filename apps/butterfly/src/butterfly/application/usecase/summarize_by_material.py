from decimal import Decimal

from butterfly.domain.entities.sales_summary import SalesSummaryByMaterial
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


class SummarizeByMaterial:
    def __init__(self, repo: SalesOrderRepo):
        self.repo = repo

    def execute(self) -> list[SalesSummaryByMaterial]:
        totals: dict[tuple, list] = {}
        for order in self.repo.list_all():
            if order.overall_status == "X":
                continue
            for item in order.items:
                key = (order.order_date, item.material, order.transaction_currency, order.company_code)
                entry = totals.setdefault(
                    key, [item.material_description, item.quantity_unit, Decimal("0.000"), Decimal("0.00")]
                )
                entry[2] += item.quantity
                entry[3] += item.net_amount
        return [
            SalesSummaryByMaterial(material, description, day, quantity, unit, amount, currency, company)
            for (day, material, currency, company), (description, unit, quantity, amount) in sorted(totals.items())
        ]
