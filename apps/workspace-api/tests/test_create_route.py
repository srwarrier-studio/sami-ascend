
from workspace_api.domain.errors import SapUnavailable, ValidationDetail
from workspace_api.infrastructure.mock_sales_order_gateway import MockSalesOrderGateway

from test_routes_access import VALID_BODY, make_client

URL = "/v1/workspace/sales-orders"


class TestCreateRoute:
    def test_returns_201_with_order_and_exact_decimals(self):
        response = make_client(MockSalesOrderGateway(), ["sales"]).post(URL, json=VALID_BODY)
        body = response.json()
        assert response.status_code == 201
        assert body["sales_order"] == "0000000001"
        assert body["overall_status"] == "A"
        assert body["items"][0]["quantity"] == "50.000"
        assert body["items"][0]["sales_order_item"] == "000010"
        assert body["creation_date_time"].endswith("Z")

    def test_rejection_is_422_with_every_detail_in_order(self):
        gateway = MockSalesOrderGateway()
        gateway.reject_with([
            ValidationDetail("CUSTOMER_UNKNOWN", "x", "SoldToParty"),
            ValidationDetail("NO_ITEMS", "y", "_Item"),
        ])
        response = make_client(gateway, ["sales"]).post(URL, json=VALID_BODY)
        assert response.status_code == 422
        assert response.json() == {
            "code": "VALIDATION_FAILED",
            "details": [
                {"code": "CUSTOMER_UNKNOWN", "target": "SoldToParty", "message": "x"},
                {"code": "NO_ITEMS", "target": "_Item", "message": "y"},
            ],
        }

    def test_sap_unavailable_is_503_without_detail(self):
        gateway = MockSalesOrderGateway()
        gateway.create = lambda order: (_ for _ in ()).throw(SapUnavailable("secret host"))
        response = make_client(gateway, ["sales"]).post(URL, json=VALID_BODY)
        assert response.status_code == 503
        assert response.json() == {"code": "SAP_UNAVAILABLE"}

    def test_response_carries_request_id(self):
        response = make_client(MockSalesOrderGateway(), ["sales"]).post(URL, json=VALID_BODY)
        assert response.headers["x-request-id"]
