from abc import ABC, abstractmethod

from workspace_api.domain.entities.sales_order import NewSalesOrder, SalesOrder, SalesOrderPage


class SalesOrderGateway(ABC):
    @abstractmethod
    def create(self, order: NewSalesOrder) -> SalesOrder: ...

    @abstractmethod
    def list_recent(self, top: int, skip: int) -> SalesOrderPage: ...
