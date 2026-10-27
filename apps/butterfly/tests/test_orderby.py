from dataclasses import replace
from datetime import date

import pytest

from butterfly.application.dto.list_query_dto import ListQuery
from butterfly.application.usecase.list_sales_orders import ListSalesOrders
from butterfly.infrastructure.api.odata import ROOT
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from conftest import ORDERS, make_client

URL = ROOT + "SalesOrder"


def keys(orderby, orders=ORDERS):
    query = ListQuery(orderby=orderby)
    result = ListSalesOrders(InMemorySalesOrderRepo(orders)).execute(query)
    return [order.sales_order for order in result.rows]


class TestOrderBy:
    def test_ascending_is_the_default(self):
        assert keys("TotalNetAmount") == keys("TotalNetAmount asc")

    def test_ascending_on_decimal(self):
        expected = [o.sales_order for o in sorted(ORDERS, key=lambda o: o.total_net_amount)]
        assert keys("TotalNetAmount asc") == expected

    def test_descending_on_decimal_is_numeric_not_text(self):
        expected = [o.sales_order for o in sorted(ORDERS, key=lambda o: -o.total_net_amount)]
        assert keys("TotalNetAmount desc") == expected

    def test_descending_on_timestamp(self):
        assert keys("CreationDateTime desc") == [o.sales_order for o in reversed(ORDERS)]

    def test_second_key_breaks_ties_in_the_first(self):
        expected = sorted(
            ORDERS, key=lambda o: (o.overall_status, -o.total_net_amount.__float__())
        )
        assert keys("OverallStatus asc, TotalNetAmount desc") == [o.sales_order for o in expected]

    def test_equal_values_keep_the_original_order(self):
        by_status = keys("OverallStatus")
        group = [k for k in by_status if k in {o.sales_order for o in ORDERS if o.overall_status == "A"}]
        assert group == sorted(group)

    def test_extra_spaces_are_fine(self):
        assert keys("  OverallStatus   desc ") == keys("OverallStatus desc")

    def test_empty_values_come_first_ascending_and_last_descending(self):
        orders = [
            replace(ORDERS[0], requested_delivery_date=date(2026, 11, 5)),
            replace(ORDERS[1], requested_delivery_date=None),
            replace(ORDERS[2], requested_delivery_date=date(2026, 11, 1)),
        ]
        ascending = keys("RequestedDeliveryDate asc", orders)
        descending = keys("RequestedDeliveryDate desc", orders)

        assert ascending == [orders[1].sales_order, orders[2].sales_order, orders[0].sales_order]
        assert descending == [orders[0].sales_order, orders[2].sales_order, orders[1].sales_order]

    def test_works_over_http_with_filter(self):
        rows = make_client().get(
            URL, params={"$filter": "OverallStatus eq 'A'", "$orderby": "SalesOrder desc"}
        ).json()["value"]

        found = [row["SalesOrder"] for row in rows]
        assert found == sorted(found, reverse=True)
        assert {row["OverallStatus"] for row in rows} == {"A"}


class TestInvalidOrderBy:
    @pytest.mark.parametrize(
        "text",
        ["Colour", "SalesOrder up", "SalesOrder desc extra", "", "SalesOrder,", "SalesOrder DESC"],
    )
    def test_is_400_invalid_query_on_orderby(self, text):
        response = make_client().get(URL, params={"$orderby": text})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_QUERY"
        assert response.json()["error"]["target"] == "$orderby"
