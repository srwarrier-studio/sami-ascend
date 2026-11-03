from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.purchases import DailyPurchases, GroupPurchases, PurchaseItem, SupplierPurchases
from synapse_api.domain.gateways.purchase_source import PurchaseSource
from synapse_api.infrastructure.odata_reader import ODataReader, company_clause


def day_range(field: str, start: date, end: date) -> str:
    return f"{field}%20ge%20{start.isoformat()}%20and%20{field}%20le%20{end.isoformat()}"


def item_from_json(row: dict) -> PurchaseItem:
    return PurchaseItem(
        row["PurchaseOrder"],
        row["PurchaseOrderItem"],
        row["SupplierName"] or "",
        date.fromisoformat(row["OrderDate"]),
        date.fromisoformat(row["PromisedDeliveryDate"]),
        date.fromisoformat(row["ActualDeliveryDate"]) if row["ActualDeliveryDate"] else None,
        Decimal(row["NetAmount"]),
        row["TransactionCurrency"],
        row["DeliveryStatus"],
    )


class ButterflyPurchaseSource(PurchaseSource):
    def __init__(self, reader: ODataReader, companies: tuple[str, ...] | None = None):
        self.reader = reader
        self.companies = companies

    def for_companies(self, companies: tuple[str, ...]) -> "ButterflyPurchaseSource":
        return ButterflyPurchaseSource(self.reader, companies)

    def company(self) -> str:
        return company_clause("CompanyCode", self.companies)

    def daily_purchases(self, start: date, end: date) -> list[DailyPurchases]:
        path = f"PurchaseSummaryByDay?$filter={day_range('OrderDate', start, end)}{self.company()}&$orderby=OrderDate,Currency,CompanyCode"
        return [DailyPurchases(date.fromisoformat(r["OrderDate"]), Decimal(r["TotalNetAmount"]), r["OrderCount"], r["Currency"]) for r in self.reader.all_rows(path)]

    def supplier_purchases(self, start: date, end: date) -> list[SupplierPurchases]:
        path = f"PurchaseSummaryBySupplier?$filter={day_range('OrderDate', start, end)}{self.company()}&$orderby=OrderDate,Supplier,Currency,CompanyCode"
        return [
            SupplierPurchases(r["Supplier"], r["SupplierName"] or "", date.fromisoformat(r["OrderDate"]), Decimal(r["TotalNetAmount"]), r["OrderCount"], r["Currency"])
            for r in self.reader.all_rows(path)
        ]

    def group_purchases(self, start: date, end: date) -> list[GroupPurchases]:
        path = f"PurchaseSummaryByMaterialGroup?$filter={day_range('OrderDate', start, end)}{self.company()}&$orderby=OrderDate,MaterialGroup,Currency,CompanyCode"
        return [
            GroupPurchases(r["MaterialGroup"], r["MaterialGroupName"] or r["MaterialGroup"], date.fromisoformat(r["OrderDate"]), Decimal(r["TotalNetAmount"]), r["OrderCount"], r["Currency"])
            for r in self.reader.all_rows(path)
        ]

    def recent_items(self, top: int) -> list[PurchaseItem]:
        path = f"PurchaseDelivery?$filter=DeliveryStatus%20ne%20'X'{self.company()}&$orderby=OrderDate%20desc,PurchaseOrder%20desc,PurchaseOrderItem%20desc&$top={top}"
        return [item_from_json(row) for row in self.reader.get_rows(path)]

    def items_due(self, start: date, end: date) -> list[PurchaseItem]:
        path = f"PurchaseDelivery?$filter={day_range('PromisedDeliveryDate', start, end)}%20and%20DeliveryStatus%20ne%20'X'{self.company()}&$orderby=PromisedDeliveryDate,PurchaseOrder,PurchaseOrderItem"
        return [item_from_json(row) for row in self.reader.all_rows(path)]

    def open_item_count(self) -> int:
        return self.reader.count(f"PurchaseDelivery?$filter=DeliveryStatus%20eq%20'O'{self.company()}")
