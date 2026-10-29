from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.sales import CustomerSales, DailySales, HighValueOrder, MaterialSales, OrderStatus


class SalesSource(ABC):
    @abstractmethod
    def daily_sales(self, start: date, end: date) -> list[DailySales]: ...

    @abstractmethod
    def customer_sales(self, start: date, end: date) -> list[CustomerSales]: ...

    @abstractmethod
    def material_sales(self, start: date, end: date) -> list[MaterialSales]: ...

    @abstractmethod
    def order_statuses(self, start: date, end: date) -> list[OrderStatus]: ...

    @abstractmethod
    def high_value_orders(self, minimum: Decimal, top: int) -> list[HighValueOrder]: ...
