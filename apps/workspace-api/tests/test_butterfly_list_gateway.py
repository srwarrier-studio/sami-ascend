import httpx
import pytest
from structured_logging.request_id import request_id_var

from test_butterfly_create_gateway import CREATED, gateway, new_order
from workspace_api.domain.errors import SapUnavailable


def page(count: int = 14) -> dict:
    return {"@odata.count": count, "value": [CREATED, {**CREATED, "SalesOrder": "0000012030"}]}


class TestListRequest:
    def test_builds_the_odata_query(self):
        seen = {}

        def handler(request):
            seen["method"] = request.method
            seen["url"] = str(request.url)
            return httpx.Response(200, json=page())

        gateway(handler).list_recent(top=5, skip=10)
        assert seen["method"] == "GET"
        assert seen["url"] == (
            "http://sap/root/SalesOrder?$orderby=SalesOrder%20desc&$top=5&$skip=10&$count=true&$expand=_Item"
        )


class TestListResponse:
    def test_maps_orders_items_and_total(self):
        result = gateway(lambda r: httpx.Response(200, json=page(14))).list_recent(2, 0)
        assert [o.sales_order for o in result.orders] == ["0000012031", "0000012030"]
        assert result.total == 14
        assert result.orders[0].items[0].material == "RM-1001"

    def test_empty_page(self):
        result = gateway(lambda r: httpx.Response(200, json={"@odata.count": 0, "value": []})).list_recent(2, 0)
        assert result.orders == []
        assert result.total == 0

    def test_server_error_is_unavailable(self):
        with pytest.raises(SapUnavailable):
            gateway(lambda r: httpx.Response(503)).list_recent(2, 0)

    def test_unexpected_status_is_unavailable(self):
        with pytest.raises(SapUnavailable):
            gateway(lambda r: httpx.Response(400, json={})).list_recent(2, 0)


class TestRequestId:
    def test_sent_on_list_and_create(self):
        seen = []

        def handler(request):
            seen.append(request.headers.get("X-Request-ID"))
            if request.method == "POST":
                return httpx.Response(201, json=CREATED)
            return httpx.Response(200, json=page())

        token = request_id_var.set("req-123")
        try:
            gateway(handler).list_recent(2, 0)
            gateway(handler).create(new_order())
        finally:
            request_id_var.reset(token)
        assert seen == ["req-123", "req-123"]

    def test_omitted_outside_a_request(self):
        seen = []

        def handler(request):
            seen.append("X-Request-ID" in request.headers)
            return httpx.Response(200, json=page())

        gateway(handler).list_recent(2, 0)
        assert seen == [False]
