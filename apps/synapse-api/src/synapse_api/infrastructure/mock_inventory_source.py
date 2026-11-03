from datetime import date

from synapse_api.domain.entities.inventory import DayMovement, GroupStock, HourMovement, MonthValue, StatusStock, StockItem, WarehouseStock
from synapse_api.domain.gateways.inventory_source import InventorySource


class MockInventorySource(InventorySource):
    def __init__(
        self,
        statuses: list[StatusStock] | None = None,
        warehouses: list[WarehouseStock] | None = None,
        groups: list[GroupStock] | None = None,
        months: list[MonthValue] | None = None,
        days: list[DayMovement] | None = None,
        hours: list[HourMovement] | None = None,
        items: list[StockItem] | None = None,
    ):
        self.statuses = statuses or []
        self.warehouses = warehouses or []
        self.groups = groups or []
        self.months = months or []
        self.days = days or []
        self.hours = hours or []
        self.items = items or []

    def for_companies(self, companies: tuple[str, ...]) -> "MockInventorySource":
        return self

    def stock_by_status(self) -> list[StatusStock]:
        return self.statuses

    def stock_by_warehouse(self) -> list[WarehouseStock]:
        return self.warehouses

    def stock_by_group(self) -> list[GroupStock]:
        return self.groups

    def month_values(self, since: str) -> list[MonthValue]:
        return [month for month in self.months if month.period >= since]

    def movements_by_day(self, start: date, end: date) -> list[DayMovement]:
        return [row for row in self.days if start <= row.day <= end]

    def movements_by_hour(self, start: date, end: date) -> list[HourMovement]:
        return [row for row in self.hours if start <= row.day <= end]

    def low_items(self) -> list[StockItem]:
        return [item for item in self.items if item.status != "O"]

    def idle_items(self, top: int) -> list[StockItem]:
        moved = [item for item in self.items if item.status != "Z" and item.last_movement is not None]
        return sorted(moved, key=lambda item: (item.last_movement, item.material))[:top]
