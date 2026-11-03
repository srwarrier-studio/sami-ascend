from datetime import date
from decimal import Decimal

from synapse_api.application.export_summary import EXPORT_IDS, GetExportSummary
from synapse_api.application.inventory_summary import INVENTORY_IDS, GetInventorySummary
from synapse_api.application.production_summary import PRODUCTION_IDS, GetProductionSummary
from synapse_api.application.purchase_summary import PURCHASE_IDS, GetPurchaseSummary
from synapse_api.application.receivables_summary import RECEIVABLES_IDS, GetReceivablesSummary
from synapse_api.application.sales_summary import GetSalesSummary
from synapse_api.domain.gateways.export_source import ExportSource
from synapse_api.domain.gateways.inventory_source import InventorySource
from synapse_api.domain.gateways.production_source import ProductionSource
from synapse_api.domain.gateways.purchase_source import PurchaseSource
from synapse_api.domain.gateways.receivables_source import ReceivablesSource
from synapse_api.domain.gateways.sales_source import SalesSource

SALES_IDS = {"sales-today", "sales-month", "sales-year", "orders-month", "month-on-month", "day-sales", "high-value-sales", "top-customers", "top-materials", "month-target", "status-split"}
PER_TOPIC = 2


class GetBoardSummary:
    def __init__(self, sales: SalesSource, target: Decimal, purchases: PurchaseSource | None = None, receivables: ReceivablesSource | None = None, inventory: InventorySource | None = None, production: ProductionSource | None = None, exports: ExportSource | None = None):
        self.sales = sales
        self.target = target
        self.purchases = purchases
        self.receivables = receivables
        self.inventory = inventory
        self.production = production
        self.exports = exports

    def execute(self, today: date, currency: str, widgets: set[str]) -> list[str]:
        topics = []
        if widgets & SALES_IDS:
            topics.append(lambda: GetSalesSummary(self.sales, self.target).execute(today, currency, widgets))
        if self.purchases is not None and widgets & PURCHASE_IDS:
            topics.append(lambda: GetPurchaseSummary(self.purchases).execute(today, currency, widgets))
        if self.receivables is not None and widgets & RECEIVABLES_IDS:
            topics.append(lambda: GetReceivablesSummary(self.receivables).execute(today, currency, widgets))
        if self.inventory is not None and widgets & INVENTORY_IDS:
            topics.append(lambda: GetInventorySummary(self.inventory).execute(today, currency, widgets))
        if self.production is not None and widgets & PRODUCTION_IDS:
            topics.append(lambda: GetProductionSummary(self.production).execute(today, currency, widgets))
        if self.exports is not None and widgets & EXPORT_IDS:
            topics.append(lambda: GetExportSummary(self.exports).execute(today, currency, widgets))
        return [sentence for write in topics for sentence in write()[:PER_TOPIC]]
