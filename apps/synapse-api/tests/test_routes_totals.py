from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import jwt
import pytest
from fastapi.testclient import TestClient
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from synapse_api.domain.entities.sales import DailySales
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.settings import Settings

SECRET = "s" * 32
TODAY = date(2026, 10, 28)

DAILY = [
    DailySales(date(2026, 1, 1), Decimal("10.00"), 1, "INR"),
    DailySales(date(2026, 10, 1), Decimal("20.00"), 2, "INR"),
    DailySales(date(2026, 10, 28), Decimal("30.50"), 3, "INR"),
    DailySales(date(2026, 10, 28), Decimal("5.00"), 1, "USD"),
    DailySales(date(2026, 10, 29), Decimal("99.00"), 9, "INR"),
]


def token_with(roles: list[str]) -> str:
    payload = {
        "sub": "user-1",
        "sap_username": "SAP_USER",
        "roles": roles,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def make_client(source: MockSalesSource, roles: list[str] | None = None) -> TestClient:
    client = TestClient(create_app(source, Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY))
    if roles is not None:
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(roles))
    return client


def total(start: str, end: str, amount: str, count: int, currency: str) -> dict:
    return {"start": start, "end": end, "net_amount": amount, "order_count": count, "currency": currency}


class TestPeriodAccess:
    @pytest.mark.parametrize("path", ["today", "month-to-date", "year-to-date"])
    def test_no_cookie_is_401(self, path):
        assert make_client(MockSalesSource(DAILY)).get(f"/v1/synapse/sales/{path}").status_code == 401

    @pytest.mark.parametrize("roles", [["sales"], ["stores"], ["accounts", "quality"]])
    def test_other_roles_are_403(self, roles):
        assert make_client(MockSalesSource(DAILY), roles).get("/v1/synapse/sales/today").status_code == 403

    @pytest.mark.parametrize("roles", [["management"], ["admin"], ["sales", "management"]])
    def test_management_and_admin_pass(self, roles):
        assert make_client(MockSalesSource(DAILY), roles).get("/v1/synapse/sales/today").status_code == 200


class TestPeriodBodies:
    def test_today(self):
        body = make_client(MockSalesSource(DAILY), ["management"]).get("/v1/synapse/sales/today").json()
        assert body == {
            "totals": [
                total("2026-10-28", "2026-10-28", "30.50", 3, "INR"),
                total("2026-10-28", "2026-10-28", "5.00", 1, "USD"),
            ]
        }

    def test_month_to_date(self):
        body = make_client(MockSalesSource(DAILY), ["management"]).get("/v1/synapse/sales/month-to-date").json()
        assert body["totals"][0] == total("2026-10-01", "2026-10-28", "50.50", 5, "INR")

    def test_year_to_date(self):
        body = make_client(MockSalesSource(DAILY), ["management"]).get("/v1/synapse/sales/year-to-date").json()
        assert body["totals"][0] == total("2026-01-01", "2026-10-28", "60.50", 6, "INR")

    def test_no_sales_is_empty_list(self):
        body = make_client(MockSalesSource(), ["management"]).get("/v1/synapse/sales/today").json()
        assert body == {"totals": []}


class TestSapDown:
    def test_failing_source_is_503_without_detail(self):
        source = MockSalesSource(DAILY)
        source.fail()
        response = make_client(source, ["management"]).get("/v1/synapse/sales/today")
        assert response.status_code == 503
        assert response.json() == {"code": "SAP_UNAVAILABLE"}
