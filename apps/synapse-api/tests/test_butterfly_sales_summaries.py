from datetime import date
from decimal import Decimal

import httpx
import pytest
from structured_logging.request_id import request_id_var

from synapse_api.domain.errors import SapUnavailable
from synapse_api.infrastructure.butterfly_sales_source import ButterflySalesSource
from synapse_api.infrastructure.settings import Settings

START, END = date(2026, 10, 26), date(2026, 10, 27)
ROOT = "http://sap/root/"

DAY = {"OrderDate": "2026-10-26", "TotalNetAmount": "845000.00", "OrderCount": 14, "Currency": "INR"}
CUSTOMER = {
    "SoldToParty": "0000100001", "CustomerName": "Acme Industries", "OrderDate": "2026-10-27",
    "TotalNetAmount": "125000.00", "OrderCount": 2, "Currency": "INR",
}
MATERIAL = {
    "Material": "RM-1001", "MaterialDescription": "Steel rod 12mm", "OrderDate": "2026-10-27",
    "TotalQuantity": "500.000", "QuantityUnit": "KG", "TotalNetAmount": "625000.00", "Currency": "INR",
}


def source(handler) -> ButterflySalesSource:
    return ButterflySalesSource(Settings(sap_base_url=ROOT), httpx.MockTransport(handler))


def ok(*rows):
    return lambda request: httpx.Response(200, json={"value": list(rows)})


class TestQuery:
    @pytest.mark.parametrize("method,entity", [
        ("daily_sales", "SalesSummaryByDay"),
        ("customer_sales", "SalesSummaryByCustomer"),
        ("material_sales", "SalesSummaryByMaterial"),
    ])
    def test_builds_the_odata_query(self, method, entity):
        seen = []

        def handler(request):
            seen.append(str(request.url))
            return httpx.Response(200, json={"value": []})

        getattr(source(handler), method)(START, END)
        assert seen == [
            f"{ROOT}{entity}?$filter=OrderDate%20ge%202026-10-26%20and%20OrderDate%20le%202026-10-27&$orderby=OrderDate"
        ]


class TestMapping:
    def test_daily_keeps_decimals_exact(self):
        [row] = source(ok(DAY)).daily_sales(START, END)
        assert row.net_amount == Decimal("845000.00")
        assert str(row.net_amount) == "845000.00"
        assert (row.date, row.order_count, row.currency) == (date(2026, 10, 26), 14, "INR")

    def test_customer(self):
        [row] = source(ok(CUSTOMER)).customer_sales(START, END)
        assert (row.customer, row.name, row.order_count) == ("0000100001", "Acme Industries", 2)

    def test_customer_without_name(self):
        [row] = source(ok({**CUSTOMER, "CustomerName": None})).customer_sales(START, END)
        assert row.name == ""

    def test_material(self):
        [row] = source(ok(MATERIAL)).material_sales(START, END)
        assert (row.material, row.description, row.unit) == ("RM-1001", "Steel rod 12mm", "KG")
        assert row.quantity == Decimal("500.000")
        assert row.net_amount == Decimal("625000.00")

    def test_empty_value_gives_empty_list(self):
        assert source(ok()).daily_sales(START, END) == []


class TestFailures:
    @pytest.mark.parametrize("status", [503, 404, 401])
    def test_bad_status(self, status):
        with pytest.raises(SapUnavailable):
            source(lambda r: httpx.Response(status)).daily_sales(START, END)

    @pytest.mark.parametrize("error", [httpx.ReadTimeout("slow"), httpx.ConnectError("down")])
    def test_transport_errors(self, error):
        def handler(request):
            raise error

        with pytest.raises(SapUnavailable):
            source(handler).daily_sales(START, END)

    @pytest.mark.parametrize("body", [{"other": 1}, ["x"]])
    def test_body_without_value(self, body):
        with pytest.raises(SapUnavailable):
            source(lambda r: httpx.Response(200, json=body)).daily_sales(START, END)

    def test_unreadable_body(self):
        with pytest.raises(SapUnavailable):
            source(lambda r: httpx.Response(200, content=b"<html>")).daily_sales(START, END)


class TestRequestId:
    def test_sent_when_present(self):
        seen = {}

        def handler(request):
            seen.update(request.headers)
            return httpx.Response(200, json={"value": []})

        token = request_id_var.set("req-1")
        try:
            source(handler).daily_sales(START, END)
        finally:
            request_id_var.reset(token)
        assert seen["x-request-id"] == "req-1"

    def test_omitted_otherwise(self):
        seen = {}

        def handler(request):
            seen.update(request.headers)
            return httpx.Response(200, json={"value": []})

        source(handler).daily_sales(START, END)
        assert "x-request-id" not in seen
