from abc import ABC, abstractmethod
from datetime import date

from synapse_api.domain.entities.inventory import DayMovement, GroupStock, HourMovement, MonthValue, StatusStock, StockItem, WarehouseStock


class InventorySource(ABC):
    @abstractmethod
    def for_companies(self, companies: tuple[str, ...]) -> "InventorySource": ...

    @abstractmethod
    def stock_by_status(self) -> list[StatusStock]: ...

    @abstractmethod
    def stock_by_warehouse(self) -> list[WarehouseStock]: ...

    @abstractmethod
    def stock_by_group(self) -> list[GroupStock]: ...

    @abstractmethod
    def month_values(self, since: str) -> list[MonthValue]: ...

    @abstractmethod
    def movements_by_day(self, start: date, end: date) -> list[DayMovement]: ...

    @abstractmethod
    def movements_by_hour(self, start: date, end: date) -> list[HourMovement]: ...

    @abstractmethod
    def low_items(self) -> list[StockItem]: ...

    @abstractmethod
    def idle_items(self, top: int) -> list[StockItem]: ...
