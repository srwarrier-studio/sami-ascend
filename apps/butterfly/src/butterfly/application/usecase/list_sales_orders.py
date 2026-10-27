from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


class ListSalesOrders:
    def __init__(self, repo: SalesOrderRepo):
        self.repo = repo

    def execute(self) -> list[SalesOrder]:
        return self.repo.list_all()
