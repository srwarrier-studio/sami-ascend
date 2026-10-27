from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from workspace_api.entrypoint.app import create_app
from workspace_api.infrastructure.mock_sales_order_gateway import MockSalesOrderGateway
from workspace_api.infrastructure.settings import Settings

SECRET = "s" * 32

VALID_BODY = {
    "sales_order_type": "OR",
    "sold_to_party": "0000100001",
    "transaction_currency": "INR",
    "requested_delivery_date": "2026-11-05",
    "items": [{"material": "RM-1001", "quantity": "50.000", "quantity_unit": "KG"}],
}


def token_with(roles: list[str]) -> str:
    payload = {
        "sub": "user-1",
        "sap_username": "SAP_USER",
        "roles": roles,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def make_client(gateway: MockSalesOrderGateway, roles: list[str] | None = None) -> TestClient:
    client = TestClient(create_app(gateway, Settings(jwt_secret=SECRET)))
    if roles is not None:
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(roles))
    return client


class TestCreateAccess:
    def test_no_cookie_is_401(self):
        response = make_client(MockSalesOrderGateway()).post("/v1/workspace/sales-orders", json=VALID_BODY)
        assert response.status_code == 401

    @pytest.mark.parametrize("roles", [["admin"], ["stores"], ["admin", "management"]])
    def test_token_without_sales_is_403(self, roles):
        gateway = MockSalesOrderGateway()
        response = make_client(gateway, roles).post("/v1/workspace/sales-orders", json=VALID_BODY)
        assert response.status_code == 403
        assert gateway.orders == []

    @pytest.mark.parametrize("roles", [["sales"], ["sales", "admin"]])
    def test_token_with_sales_passes(self, roles):
        response = make_client(MockSalesOrderGateway(), roles).post("/v1/workspace/sales-orders", json=VALID_BODY)
        assert response.status_code == 201


class TestCreateBody:
    @pytest.mark.parametrize(
        "body",
        [
            {**VALID_BODY, "sold_to_party": None},
            {**VALID_BODY, "items": [{"material": "RM-1001", "quantity": "lots", "quantity_unit": "KG"}]},
        ],
    )
    def test_malformed_body_is_422_and_gateway_not_called(self, body):
        gateway = MockSalesOrderGateway()
        response = make_client(gateway, ["sales"]).post("/v1/workspace/sales-orders", json=body)
        assert response.status_code == 422
        assert gateway.orders == []
