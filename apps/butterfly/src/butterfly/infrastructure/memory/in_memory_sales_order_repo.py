from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


class InMemorySalesOrderRepo(SalesOrderRepo):
    def __init__(self, orders: list[SalesOrder]):
        self.orders = {order.sales_order: order for order in orders}

    def list_all(self) -> list[SalesOrder]:
        return list(self.orders.values())

    def get(self, sales_order: str) -> SalesOrder | None:
        return self.orders.get(sales_order)
