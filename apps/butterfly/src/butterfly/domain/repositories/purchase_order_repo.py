from abc import ABC, abstractmethod
from datetime import datetime

from butterfly.domain.entities.purchase_order import PurchaseOrder


class PurchaseOrderRepo(ABC):
    @abstractmethod
    def list_all(self) -> list[PurchaseOrder]: ...

    @abstractmethod
    def get(self, purchase_order: str) -> PurchaseOrder | None: ...

    @abstractmethod
    def next_number(self) -> str: ...

    @abstractmethod
    def add(self, order: PurchaseOrder) -> None: ...

    @abstractmethod
    def cancel_item(self, purchase_order: str, purchase_order_item: str, changed_at: datetime) -> None: ...
