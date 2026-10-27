from datetime import date
from decimal import Decimal

import pytest

from workspace_api.application.usecase.create_sales_order import CreateSalesOrder
from workspace_api.application.usecase.list_sales_orders import ListSalesOrders
from workspace_api.domain.entities.sales_order import NewSalesOrder, NewSalesOrderItem
from workspace_api.domain.errors import InvalidQuery, SalesOrderRejected, ValidationDetail
from workspace_api.infrastructure.mock_sales_order_gateway import MockSalesOrderGateway


def new_order() -> NewSalesOrder:
    return NewSalesOrder(
        "OR", "0000100001", "INR", date(2026, 11, 5),
        [NewSalesOrderItem("RM-1001", Decimal("50.000"), "KG")],
    )


def create_orders(gateway: MockSalesOrderGateway, count: int) -> None:
    for _ in range(count):
        CreateSalesOrder(gateway).execute(new_order())


class TestCreateSalesOrder:
    def test_returns_numbered_order_with_status_a(self):
        order = CreateSalesOrder(MockSalesOrderGateway()).execute(new_order())
        assert order.sales_order == "0000000001"
        assert order.overall_status == "A"
        assert order.items[0].sales_order_item == "000010"

    def test_rejection_carries_every_detail(self):
        gateway = MockSalesOrderGateway()
        details = [ValidationDetail("CUSTOMER_UNKNOWN", "x", "SoldToParty"), ValidationDetail("NO_ITEMS", "y", "_Item")]
        gateway.reject_with(details)
        with pytest.raises(SalesOrderRejected) as raised:
            CreateSalesOrder(gateway).execute(new_order())
        assert raised.value.details == details


class TestListSalesOrders:
    def test_newest_first_with_total(self):
        gateway = MockSalesOrderGateway()
        create_orders(gateway, 3)
        page = ListSalesOrders(gateway).execute()
        assert [o.sales_order for o in page.orders] == ["0000000003", "0000000002", "0000000001"]
        assert page.total == 3

    def test_skip_and_top_page_but_total_stays(self):
        gateway = MockSalesOrderGateway()
        create_orders(gateway, 5)
        page = ListSalesOrders(gateway).execute(top=2, skip=1)
        assert [o.sales_order for o in page.orders] == ["0000000004", "0000000003"]
        assert page.total == 5

    @pytest.mark.parametrize("top", [0, 101, -1])
    def test_top_outside_range_is_rejected(self, top):
        with pytest.raises(InvalidQuery):
            ListSalesOrders(MockSalesOrderGateway()).execute(top=top)

    def test_negative_skip_is_rejected(self):
        with pytest.raises(InvalidQuery):
            ListSalesOrders(MockSalesOrderGateway()).execute(skip=-1)

    def test_top_edges_are_accepted(self):
        ListSalesOrders(MockSalesOrderGateway()).execute(top=1)
        ListSalesOrders(MockSalesOrderGateway()).execute(top=100)
