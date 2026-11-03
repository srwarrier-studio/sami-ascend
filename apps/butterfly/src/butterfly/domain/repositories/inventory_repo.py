from abc import ABC, abstractmethod

from butterfly.domain.entities.inventory import MaterialStock, StockMovement, StockValueMonth


class InventoryRepo(ABC):
    @abstractmethod
    def stocks(self) -> list[MaterialStock]: ...

    @abstractmethod
    def movements(self) -> list[StockMovement]: ...

    @abstractmethod
    def monthly_values(self) -> list[StockValueMonth]: ...

    def listing(self, entity: str):
        return getattr(self, entity)()

    def summary_listing(self, name: str):
        return None
