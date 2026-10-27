import json
from datetime import date
from decimal import Decimal

import httpx
import pytest

from workspace_api.domain.entities.sales_order import NewSalesOrder, NewSalesOrderItem
from workspace_api.domain.errors import SalesOrderRejected, SapUnavailable
from workspace_api.infrastructure.butterfly_sales_order_gateway import ButterflySalesOrderGateway
from workspace_api.infrastructure.settings import Settings

CREATED = {
    "@odata.context": "$metadata#SalesOrder(_Item())/$entity",
    "@odata.etag": 'W/"20261027091530"',
    "SalesOrder": "0000012031",
    "SalesOrderType": "OR",
    "SoldToParty": "0000100001",
    "CustomerName": "Acme Industries",
    "OrderDate": "2026-10-27",
    "RequestedDeliveryDate": "2026-11-05",
    "TransactionCurrency": "INR",
    "TotalNetAmount": "125000.00",
    "OverallStatus": "A",
    "CreatedByUser": "BUTTERFLY",
    "CreationDateTime": "2026-10-27T09:15:30Z",
    "LastChangeDateTime": "2026-10-27T09:15:30Z",
    "_Item": [
        {
            "SalesOrder": "0000012031",
            "SalesOrderItem": "000010",
            "Material": "RM-1001",
            "MaterialDescription": "Steel rod 12mm",
            "Quantity": "50.000",
            "QuantityUnit": "KG",
            "NetAmount": "62500.00",
        }
    ],
}

REJECTION = {
    "error": {
        "code": "VALIDATION_FAILED",
        "message": "The sales order has errors.",
        "details": [
            {"code": "CUSTOMER_UNKNOWN", "message": "Customer 1 does not exist.", "target": "SoldToParty"},
            {"code": "QUANTITY_NOT_POSITIVE", "message": "Quantity must be greater than 0.", "target": "_Item/0/Quantity"},
        ],
    }
}


def new_order(delivery: date | None = date(2026, 11, 5)) -> NewSalesOrder:
    return NewSalesOrder("OR", "0000100001", "INR", delivery, [NewSalesOrderItem("RM-1001", Decimal("50.000"), "KG")])


def gateway(handler) -> ButterflySalesOrderGateway:
    return ButterflySalesOrderGateway(Settings(sap_base_url="http://sap/root/"), httpx.MockTransport(handler))


class TestCreateRequest:
    def test_posts_the_contract_body(self):
        seen = {}

        def handler(request):
            seen["url"] = str(request.url)
            seen["body"] = json.loads(request.content)
            return httpx.Response(201, json=CREATED)

        gateway(handler).create(new_order())
        assert seen["url"] == "http://sap/root/SalesOrder"
        assert seen["body"] == {
            "SalesOrderType": "OR",
            "SoldToParty": "0000100001",
            "TransactionCurrency": "INR",
            "RequestedDeliveryDate": "2026-11-05",
            "_Item": [{"Material": "RM-1001", "Quantity": "50.000", "QuantityUnit": "KG"}],
        }

    def test_omits_delivery_date_when_not_given(self):
        seen = {}

        def handler(request):
            seen["body"] = json.loads(request.content)
            return httpx.Response(201, json=CREATED)

        gateway(handler).create(new_order(delivery=None))
        assert "RequestedDeliveryDate" not in seen["body"]


class TestCreateResponse:
    def test_201_maps_to_order_with_exact_decimals(self):
        order = gateway(lambda r: httpx.Response(201, json=CREATED)).create(new_order())
        assert order.sales_order == "0000012031"
        assert order.total_net_amount == Decimal("125000.00")
        assert order.items[0].quantity == Decimal("50.000")
        assert order.items[0].material_description == "Steel rod 12mm"
        assert order.creation_date_time.isoformat() == "2026-10-27T09:15:30+00:00"

    def test_null_delivery_date_and_names_are_kept_as_none(self):
        data = {**CREATED, "RequestedDeliveryDate": None, "CustomerName": None}
        data["_Item"] = [{**CREATED["_Item"][0], "MaterialDescription": None}]
        order = gateway(lambda r: httpx.Response(201, json=data)).create(new_order(None))
        assert order.requested_delivery_date is None
        assert order.customer_name is None
        assert order.items[0].material_description is None

    def test_400_keeps_every_detail_in_order(self):
        with pytest.raises(SalesOrderRejected) as raised:
            gateway(lambda r: httpx.Response(400, json=REJECTION)).create(new_order())
        assert [d.code for d in raised.value.details] == ["CUSTOMER_UNKNOWN", "QUANTITY_NOT_POSITIVE"]
        assert raised.value.details[1].target == "_Item/0/Quantity"


class TestSapFailures:
    @pytest.mark.parametrize("status", [500, 503])
    def test_server_errors_are_unavailable(self, status):
        with pytest.raises(SapUnavailable):
            gateway(lambda r: httpx.Response(status)).create(new_order())

    def test_timeout_is_unavailable(self):
        def handler(request):
            raise httpx.ReadTimeout("slow")

        with pytest.raises(SapUnavailable):
            gateway(handler).create(new_order())

    def test_connection_error_is_unavailable(self):
        def handler(request):
            raise httpx.ConnectError("down")

        with pytest.raises(SapUnavailable):
            gateway(handler).create(new_order())

    def test_unreadable_400_body_is_unavailable(self):
        with pytest.raises(SapUnavailable):
            gateway(lambda r: httpx.Response(400, text="oops")).create(new_order())

    def test_unexpected_status_is_unavailable(self):
        with pytest.raises(SapUnavailable):
            gateway(lambda r: httpx.Response(403, json={})).create(new_order())
