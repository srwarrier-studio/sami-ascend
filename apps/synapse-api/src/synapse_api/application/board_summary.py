from datetime import date
from decimal import Decimal

from synapse_api.application.purchase_summary import PURCHASE_IDS, GetPurchaseSummary
from synapse_api.application.receivables_summary import RECEIVABLES_IDS, GetReceivablesSummary
from synapse_api.application.sales_summary import GetSalesSummary
from synapse_api.domain.gateways.purchase_source import PurchaseSource
from synapse_api.domain.gateways.receivables_source import ReceivablesSource
from synapse_api.domain.gateways.sales_source import SalesSource

SALES_IDS = {"sales-today", "sales-month", "sales-year", "orders-month", "month-on-month", "day-sales", "high-value-sales", "top-customers", "top-materials", "month-target", "status-split"}
PER_TOPIC = 2


class GetBoardSummary:
    def __init__(self, sales: SalesSource, target: Decimal, purchases: PurchaseSource | None = None, receivables: ReceivablesSource | None = None):
        self.sales = sales
        self.target = target
        self.purchases = purchases
        self.receivables = receivables

    def execute(self, today: date, currency: str, widgets: set[str]) -> list[str]:
        topics = []
        if widgets & SALES_IDS:
            topics.append(lambda: GetSalesSummary(self.sales, self.target).execute(today, currency, widgets))
        if self.purchases is not None and widgets & PURCHASE_IDS:
            topics.append(lambda: GetPurchaseSummary(self.purchases).execute(today, currency, widgets))
        if self.receivables is not None and widgets & RECEIVABLES_IDS:
            topics.append(lambda: GetReceivablesSummary(self.receivables).execute(today, currency, widgets))
        return [sentence for write in topics for sentence in write()[:PER_TOPIC]]
