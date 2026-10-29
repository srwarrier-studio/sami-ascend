from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.sales import CustomerSales, DailySales, HighValueOrder, MaterialSales, OrderStatus
from synapse_api.domain.errors import SapUnavailable
from synapse_api.domain.gateways.sales_source import SalesSource


class MockSalesSource(SalesSource):
    def __init__(
        self,
        daily: list[DailySales] | None = None,
        customers: list[CustomerSales] | None = None,
        materials: list[MaterialSales] | None = None,
        orders: list[HighValueOrder] | None = None,
        statuses: list[OrderStatus] | None = None,
    ):
        self.daily = daily or []
        self.customers = customers or []
        self.materials = materials or []
        self.orders = orders or []
        self.statuses = statuses or []
        self.failing = False
        self.calls = 0

    def fail(self) -> None:
        self.failing = True

    def recover(self) -> None:
        self.failing = False

    def daily_sales(self, start: date, end: date) -> list[DailySales]:
        return self._in_range(self.daily, start, end)

    def customer_sales(self, start: date, end: date) -> list[CustomerSales]:
        return self._in_range(self.customers, start, end)

    def material_sales(self, start: date, end: date) -> list[MaterialSales]:
        return self._in_range(self.materials, start, end)

    def order_statuses(self, start: date, end: date) -> list[OrderStatus]:
        return self._in_range(self.statuses, start, end)

    def high_value_orders(self, minimum: Decimal, top: int) -> list[HighValueOrder]:
        self._check()
        wanted = [o for o in self.orders if o.net_amount >= minimum and o.status != "X"]
        return sorted(wanted, key=lambda o: o.order_date, reverse=True)[:top]

    def _in_range(self, rows: list, start: date, end: date) -> list:
        self._check()
        return sorted((r for r in rows if start <= r.date <= end), key=lambda r: r.date)

    def _check(self) -> None:
        self.calls += 1
        if self.failing:
            raise SapUnavailable()
