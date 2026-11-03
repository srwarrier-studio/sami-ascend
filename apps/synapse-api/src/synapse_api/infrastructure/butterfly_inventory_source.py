from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.inventory import DayMovement, GroupStock, HourMovement, MonthValue, StatusStock, StockItem, WarehouseStock
from synapse_api.domain.gateways.inventory_source import InventorySource
from synapse_api.infrastructure.butterfly_purchase_source import day_range
from synapse_api.infrastructure.odata_reader import ODataReader, company_clause

COMPANY_PREFIX = "%20and%20"


def item_from_json(row: dict) -> StockItem:
    return StockItem(
        row["Material"],
        row["MaterialDescription"] or row["Material"],
        Decimal(row["StockQuantity"]),
        row["QuantityUnit"],
        Decimal(row["ReorderLevel"]),
        row["StockStatus"],
        date.fromisoformat(row["LastMovementDate"]) if row["LastMovementDate"] else None,
        row["Currency"],
    )


class ButterflyInventorySource(InventorySource):
    def __init__(self, reader: ODataReader, companies: tuple[str, ...] | None = None):
        self.reader = reader
        self.companies = companies

    def for_companies(self, companies: tuple[str, ...]) -> "ButterflyInventorySource":
        return ButterflyInventorySource(self.reader, companies)

    def path(self, entity: str, order: str, *conditions: str) -> str:
        clause = " and ".join(conditions) + company_clause("CompanyCode", self.companies)
        clause = clause.removeprefix(COMPANY_PREFIX) if not conditions else clause
        filter_ = f"$filter={clause}&" if clause else ""
        return f"{entity}?{filter_}$orderby={order}"

    def stock_by_status(self) -> list[StatusStock]:
        rows = self.reader.all_rows(self.path("StockSummaryByStatus", "StockStatus,Currency,CompanyCode"))
        return [StatusStock(r["StockStatus"], Decimal(r["StockValue"]), r["MaterialCount"], r["Currency"]) for r in rows]

    def stock_by_warehouse(self) -> list[WarehouseStock]:
        rows = self.reader.all_rows(self.path("StockSummaryByWarehouse", "Plant,StorageLocation,Currency,CompanyCode"))
        return [WarehouseStock(r["Plant"], r["StorageLocation"], r["StorageLocationName"] or r["StorageLocation"], Decimal(r["StockValue"]), r["MaterialCount"], r["Currency"]) for r in rows]

    def stock_by_group(self) -> list[GroupStock]:
        rows = self.reader.all_rows(self.path("StockSummaryByMaterialGroup", "MaterialGroup,Currency,CompanyCode"))
        return [GroupStock(r["MaterialGroup"], r["MaterialGroupName"] or r["MaterialGroup"], Decimal(r["StockValue"]), r["MaterialCount"], r["Currency"]) for r in rows]

    def month_values(self, since: str) -> list[MonthValue]:
        rows = self.reader.all_rows(self.path("StockValueByMonth", "PostingPeriod,Currency,CompanyCode", f"PostingPeriod%20ge%20'{since}'"))
        return [MonthValue(r["PostingPeriod"], Decimal(r["StockValue"]), r["Currency"]) for r in rows]

    def movements_by_day(self, start: date, end: date) -> list[DayMovement]:
        rows = self.reader.all_rows(self.path("StockMovementSummaryByDay", "PostingDate,Currency,CompanyCode", day_range("PostingDate", start, end)))
        return [DayMovement(date.fromisoformat(r["PostingDate"]), Decimal(r["ReceiptValue"]), Decimal(r["IssueValue"]), r["MovementCount"], r["Currency"]) for r in rows]

    def movements_by_hour(self, start: date, end: date) -> list[HourMovement]:
        rows = self.reader.all_rows(self.path("StockMovementSummaryByHour", "PostingDate,PostingHour,CompanyCode", day_range("PostingDate", start, end)))
        return [HourMovement(date.fromisoformat(r["PostingDate"]), r["PostingHour"], r["MovementCount"]) for r in rows]

    def low_items(self) -> list[StockItem]:
        rows = self.reader.all_rows(self.path("MaterialStock", "Material,Plant,StorageLocation", "StockStatus%20ne%20'O'"))
        return [item_from_json(row) for row in rows]

    def idle_items(self, top: int) -> list[StockItem]:
        path = self.path("MaterialStock", "LastMovementDate,Material,Plant,StorageLocation", "StockStatus%20ne%20'Z'")
        return [item_from_json(row) for row in self.reader.get_rows(f"{path}&$top={top}")]
