import pytest
from workspace_api.domain.errors import SapUnavailable
from workspace_api.infrastructure.mock_sales_order_gateway import MockSalesOrderGateway

from test_routes_access import VALID_BODY, make_client

URL = "/v1/workspace/sales-orders"


def client_with_orders(count: int, roles: list[str] | None = None):
    gateway = MockSalesOrderGateway()
    client = make_client(gateway, roles or ["sales"])
    for _ in range(count):
        client.post(URL, json=VALID_BODY)
    return client, gateway


class TestListAccess:
    def test_no_cookie_is_401(self):
        assert make_client(MockSalesOrderGateway()).get(URL).status_code == 401

    def test_admin_alone_is_403(self):
        assert make_client(MockSalesOrderGateway(), ["admin"]).get(URL).status_code == 403


class TestListRoute:
    def test_newest_first_with_total_and_defaults(self):
        client, _ = client_with_orders(3)
        body = client.get(URL).json()
        assert [o["sales_order"] for o in body["orders"]] == ["0000000003", "0000000002", "0000000001"]
        assert body["total"] == 3

    def test_top_and_skip_page_but_total_stays(self):
        client, _ = client_with_orders(5)
        body = client.get(URL, params={"top": 2, "skip": 1}).json()
        assert [o["sales_order"] for o in body["orders"]] == ["0000000004", "0000000003"]
        assert body["total"] == 5

    def test_empty_list(self):
        client, _ = client_with_orders(0)
        assert client.get(URL).json() == {"orders": [], "total": 0}

    @pytest.mark.parametrize("params", [{"top": 0}, {"top": 101}, {"skip": -1}])
    def test_out_of_range_is_invalid_query(self, params):
        client, _ = client_with_orders(1)
        response = client.get(URL, params=params)
        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_QUERY"

    def test_sap_unavailable_is_503(self):
        client, gateway = client_with_orders(0)
        gateway.list_recent = lambda top, skip: (_ for _ in ()).throw(SapUnavailable())
        response = client.get(URL)
        assert response.status_code == 503
        assert response.json() == {"code": "SAP_UNAVAILABLE"}

    def test_response_carries_request_id(self):
        client, _ = client_with_orders(0)
        assert client.get(URL).headers["x-request-id"]
