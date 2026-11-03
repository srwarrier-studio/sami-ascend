from abc import ABC, abstractmethod

from butterfly.domain.entities.sales_order import SalesOrder


class SalesOrderRepo(ABC):
    def listing(self):
        return self.list_all()

    @abstractmethod
    def list_all(self) -> list[SalesOrder]: ...

    @abstractmethod
    def get(self, sales_order: str) -> SalesOrder | None: ...

    @abstractmethod
    def next_number(self) -> str: ...

    @abstractmethod
    def add(self, order: SalesOrder) -> None: ...

    @abstractmethod
    def update(self, order: SalesOrder) -> None: ...
