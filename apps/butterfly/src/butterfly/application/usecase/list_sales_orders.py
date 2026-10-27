from dataclasses import replace

from butterfly.application.dto.list_query_dto import ListQuery, ListResult
from butterfly.application.filter.fields import SALES_ORDER_FIELDS
from butterfly.application.list_query import apply_list_query
from butterfly.application.query_options import parse_expand
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


class ListSalesOrders:
    def __init__(self, repo: SalesOrderRepo):
        self.repo = repo

    def execute(self, query: ListQuery | None = None, expand: str | None = None) -> ListResult:
        expanded = parse_expand(expand)
        result = apply_list_query(self.repo.list_all(), query or ListQuery(), SALES_ORDER_FIELDS)
        return replace(result, expand=expanded)
