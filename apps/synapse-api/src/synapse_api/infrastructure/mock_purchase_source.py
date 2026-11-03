from datetime import date

from synapse_api.domain.entities.purchases import DailyPurchases, GroupPurchases, PurchaseItem, SupplierPurchases
from synapse_api.domain.gateways.purchase_source import PurchaseSource


class MockPurchaseSource(PurchaseSource):
    def __init__(self, daily: list[DailyPurchases] | None = None, suppliers: list[SupplierPurchases] | None = None, items: list[PurchaseItem] | None = None, groups: list[GroupPurchases] | None = None):
        self.daily = daily or []
        self.suppliers = suppliers or []
        self.items = items or []
        self.groups = groups or []

    def for_companies(self, companies: tuple[str, ...]) -> "MockPurchaseSource":
        return self

    def daily_purchases(self, start: date, end: date) -> list[DailyPurchases]:
        return [row for row in self.daily if start <= row.date <= end]

    def supplier_purchases(self, start: date, end: date) -> list[SupplierPurchases]:
        return [row for row in self.suppliers if start <= row.date <= end]

    def group_purchases(self, start: date, end: date) -> list[GroupPurchases]:
        return [row for row in self.groups if start <= row.date <= end]

    def recent_items(self, top: int) -> list[PurchaseItem]:
        live = [item for item in self.items if item.status != "X"]
        return sorted(live, key=lambda item: (item.order_date, item.order), reverse=True)[:top]

    def items_due(self, start: date, end: date) -> list[PurchaseItem]:
        return [item for item in self.items if item.status != "X" and start <= item.promised <= end]

    def open_item_count(self) -> int:
        return sum(1 for item in self.items if item.status == "O")
