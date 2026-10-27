from butterfly.application.dto.list_query_dto import ListQuery, ListResult
from butterfly.application.filter.fields import SALES_ORDER_ITEM_FIELDS
from butterfly.application.list_query import apply_list_query
from butterfly.application.usecase.get_sales_order import GetSalesOrder
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


class ListSalesOrderItems:
    def __init__(self, repo: SalesOrderRepo):
        self.repo = repo

    def execute(self, sales_order: str, query: ListQuery | None = None) -> ListResult:
        order = GetSalesOrder(self.repo).execute(sales_order)
        return apply_list_query(order.items, query or ListQuery(), SALES_ORDER_ITEM_FIELDS)
