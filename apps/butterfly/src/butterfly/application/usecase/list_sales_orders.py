from butterfly.application.filter.parser import parse_filter
from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


class ListSalesOrders:
    def __init__(self, repo: SalesOrderRepo):
        self.repo = repo

    def execute(self, filter_text: str | None = None) -> list[SalesOrder]:
        orders = self.repo.list_all()
        if filter_text is None:
            return orders
        condition = parse_filter(filter_text)
        return [order for order in orders if condition.matches(order)]
