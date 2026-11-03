from datetime import date

import httpx
import pytest
from structured_logging.request_id import request_id_var

from synapse_api.domain.errors import SapUnavailable
from synapse_api.infrastructure.butterfly_sales_source import ButterflySalesSource
from synapse_api.infrastructure.odata_reader import PAGE
from synapse_api.infrastructure.settings import Settings

START, END = date(2025, 9, 1), date(2026, 10, 31)
ROOT = "http://sap/root/"

CALLS = [
    ("daily_sales", "SalesSummaryByDay"),
    ("customer_sales", "SalesSummaryByCustomer"),
    ("material_sales", "SalesSummaryByMaterial"),
]

ROWS = {
    "SalesSummaryByDay": {"OrderDate": "2026-01-05", "TotalNetAmount": "100.00", "TotalNetAmountLocal": "100.00", "LocalCurrency": "INR", "TotalNetAmountLocal": "100.00", "LocalCurrency": "INR", "OrderCount": 1, "Currency": "INR"},
    "SalesSummaryByCustomer": {"SoldToParty": "0000100001", "CustomerName": "Acme Industries", "OrderDate": "2026-01-05", "TotalNetAmount": "100.00", "TotalNetAmountLocal": "100.00", "LocalCurrency": "INR", "TotalNetAmountLocal": "100.00", "LocalCurrency": "INR", "OrderCount": 1, "Currency": "INR"},
    "SalesSummaryByMaterial": {"Material": "RM-1001", "MaterialDescription": "Steel rod", "OrderDate": "2026-01-05", "TotalQuantity": "1.000", "QuantityUnit": "KG", "TotalNetAmount": "100.00", "TotalNetAmountLocal": "100.00", "LocalCurrency": "INR", "TotalNetAmountLocal": "100.00", "LocalCurrency": "INR", "Currency": "INR"},
}


def source(handler) -> ButterflySalesSource:
    return ButterflySalesSource(Settings(sap_base_url=ROOT), httpx.MockTransport(handler))


def paged(entity: str, sizes: list[int], seen: list):
    def handler(request):
        skip = int(request.url.params["$skip"])
        seen.append((int(request.url.params["$top"]), skip))
        index = skip // PAGE
        size = sizes[index] if index < len(sizes) else 0
        return httpx.Response(200, json={"value": [ROWS[entity]] * size})

    return handler


@pytest.mark.parametrize("method,entity", CALLS)
class TestPaging:
    def test_a_short_first_page_is_one_request(self, method, entity):
        seen = []
        assert len(getattr(source(paged(entity, [7], seen)), method)(START, END)) == 7
        assert seen == [(PAGE, 0)]

    def test_more_than_one_page_is_read_in_full(self, method, entity):
        seen = []
        rows = getattr(source(paged(entity, [PAGE, 3], seen)), method)(START, END)
        assert len(rows) == PAGE + 3
        assert seen == [(PAGE, 0), (PAGE, PAGE)]

    def test_exactly_one_full_page_needs_one_more_empty_request(self, method, entity):
        seen = []
        assert len(getattr(source(paged(entity, [PAGE], seen)), method)(START, END)) == PAGE
        assert seen == [(PAGE, 0), (PAGE, PAGE)]

    def test_three_pages(self, method, entity):
        seen = []
        assert len(getattr(source(paged(entity, [PAGE, PAGE, 1], seen)), method)(START, END)) == 2 * PAGE + 1
        assert [skip for _, skip in seen] == [0, PAGE, 2 * PAGE]

    def test_nothing_gives_an_empty_list_after_one_request(self, method, entity):
        seen = []
        assert getattr(source(paged(entity, [0], seen)), method)(START, END) == []
        assert len(seen) == 1

    @pytest.mark.parametrize("failure", ["status", "connection", "body"])
    def test_a_failure_on_a_later_page_fails_the_whole_call(self, method, entity, failure):
        def handler(request):
            if int(request.url.params["$skip"]) == 0:
                return httpx.Response(200, json={"value": [ROWS[entity]] * PAGE})
            if failure == "connection":
                raise httpx.ConnectError("down")
            if failure == "body":
                return httpx.Response(200, text="not json")
            return httpx.Response(503)

        with pytest.raises(SapUnavailable):
            getattr(source(handler), method)(START, END)

    def test_the_request_id_is_sent_on_every_page(self, method, entity):
        ids = []

        def handler(request):
            ids.append(request.headers.get("x-request-id"))
            size = PAGE if int(request.url.params["$skip"]) == 0 else 1
            return httpx.Response(200, json={"value": [ROWS[entity]] * size})

        token = request_id_var.set("req-42")
        try:
            getattr(source(handler), method)(START, END)
        finally:
            request_id_var.reset(token)
        assert ids == ["req-42", "req-42"]


class TestOrderStatusesUnchanged:
    def test_sends_the_same_requests_as_before(self):
        seen = []

        def handler(request):
            seen.append(str(request.url))
            return httpx.Response(200, json={"value": []})

        source(handler).order_statuses(date(2026, 10, 1), date(2026, 10, 27))
        assert seen == [
            f"{ROOT}SalesOrder?$filter=OrderDate%20ge%202026-10-01%20and%20OrderDate%20le%202026-10-27%20and%20OverallStatus%20ne%20'X'"
            f"&$select=OrderDate,OverallStatus&$orderby=OrderDate&$top={PAGE}&$skip=0"
        ]
