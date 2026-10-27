from abc import ABC, abstractmethod

from butterfly.domain.entities.sales_order import SalesOrder


class SalesOrderRepo(ABC):
    @abstractmethod
    def list_all(self) -> list[SalesOrder]: ...

    @abstractmethod
    def get(self, sales_order: str) -> SalesOrder | None: ...
