from abc import ABC, abstractmethod
from datetime import date

from synapse_api.domain.entities.purchases import DailyPurchases, PurchaseItem, SupplierPurchases


class PurchaseSource(ABC):
    @abstractmethod
    def for_companies(self, companies: tuple[str, ...]) -> "PurchaseSource": ...

    @abstractmethod
    def daily_purchases(self, start: date, end: date) -> list[DailyPurchases]: ...

    @abstractmethod
    def supplier_purchases(self, start: date, end: date) -> list[SupplierPurchases]: ...

    @abstractmethod
    def recent_items(self, top: int) -> list[PurchaseItem]: ...

    @abstractmethod
    def items_due(self, start: date, end: date) -> list[PurchaseItem]: ...

    @abstractmethod
    def open_item_count(self) -> int: ...
