from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.domain.errors import SalesOrderNotFound
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


class GetSalesOrder:
    def __init__(self, repo: SalesOrderRepo):
        self.repo = repo

    def execute(self, sales_order: str) -> SalesOrder:
        order = self.repo.get(sales_order)
        if order is None:
            raise SalesOrderNotFound(sales_order)
        return order
