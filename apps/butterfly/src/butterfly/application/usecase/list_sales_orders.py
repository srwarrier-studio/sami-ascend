from butterfly.application.dto.list_sales_orders_dto import (
    ListSalesOrdersQuery,
    ListSalesOrdersResult,
)
from butterfly.application.filter.fields import SALES_ORDER_FIELDS
from butterfly.application.filter.parser import parse_filter
from butterfly.application.query_options import (
    parse_count,
    parse_orderby,
    parse_select,
    parse_skip,
    parse_top,
)
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo


def sort_key(attribute: str):
    def key(order):
        value = getattr(order, attribute)
        return (value is not None, value)

    return key


class ListSalesOrders:
    def __init__(self, repo: SalesOrderRepo):
        self.repo = repo

    def execute(self, query: ListSalesOrdersQuery | None = None) -> ListSalesOrdersResult:
        query = query or ListSalesOrdersQuery()
        select = parse_select(query.select)
        orderby = parse_orderby(query.orderby)
        top = parse_top(query.top)
        skip = parse_skip(query.skip)
        count = parse_count(query.count)
        condition = None if query.filter is None else parse_filter(query.filter)

        orders = self.repo.list_all()
        if condition is not None:
            orders = [order for order in orders if condition.matches(order)]
        for name, descending in reversed(orderby):
            attribute = SALES_ORDER_FIELDS[name][0]
            orders = sorted(orders, key=sort_key(attribute), reverse=descending)
        return ListSalesOrdersResult(
            orders=orders[skip : skip + top],
            total=len(orders) if count else None,
            select=select,
        )
