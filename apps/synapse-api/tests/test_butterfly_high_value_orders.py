from datetime import date
from decimal import Decimal

import httpx
import pytest

from synapse_api.domain.errors import SapUnavailable
from synapse_api.infrastructure.butterfly_sales_source import ButterflySalesSource
from synapse_api.infrastructure.settings import Settings

ROOT = "http://sap/root/"

ORDER = {
    "SalesOrder": "0000012345", "CustomerName": "Acme Industries", "OrderDate": "2026-10-27",
    "TransactionCurrency": "INR", "TotalNetAmount": "125000.00", "OverallStatus": "A",
}


def source(handler) -> ButterflySalesSource:
    return ButterflySalesSource(Settings(sap_base_url=ROOT), httpx.MockTransport(handler))


class TestQuery:
    def test_builds_the_odata_query(self):
        seen = []

        def handler(request):
            seen.append(str(request.url))
            return httpx.Response(200, json={"value": []})

        source(handler).high_value_orders(Decimal("100000.00"), 5)
        assert seen == [
            f"{ROOT}SalesOrder?$filter=TotalNetAmount%20ge%20100000.00%20and%20OverallStatus%20ne%20'X'"
            "&$orderby=CreationDateTime%20desc&$top=5"
        ]


class TestMapping:
    def test_maps_order_with_exact_decimal(self):
        [row] = source(lambda r: httpx.Response(200, json={"value": [ORDER]})).high_value_orders(Decimal("1"), 5)
        assert (row.order, row.customer_name, row.order_date) == ("0000012345", "Acme Industries", date(2026, 10, 27))
        assert str(row.net_amount) == "125000.00"
        assert (row.currency, row.status) == ("INR", "A")

    def test_order_without_customer_name(self):
        body = {"value": [{**ORDER, "CustomerName": None}]}
        [row] = source(lambda r: httpx.Response(200, json=body)).high_value_orders(Decimal("1"), 5)
        assert row.customer_name == ""

    def test_empty_value_gives_empty_list(self):
        assert source(lambda r: httpx.Response(200, json={"value": []})).high_value_orders(Decimal("1"), 5) == []


class TestFailures:
    @pytest.mark.parametrize("status", [503, 404])
    def test_bad_status(self, status):
        with pytest.raises(SapUnavailable):
            source(lambda r: httpx.Response(status)).high_value_orders(Decimal("1"), 5)

    def test_body_without_value(self):
        with pytest.raises(SapUnavailable):
            source(lambda r: httpx.Response(200, json={})).high_value_orders(Decimal("1"), 5)
