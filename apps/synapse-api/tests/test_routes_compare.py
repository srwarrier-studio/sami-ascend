from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from test_routes_cache import make
from test_routes_totals import make_client

from synapse_api.domain.entities.sales import CustomerSales, DailySales
from synapse_api.infrastructure.mock_sales_source import MockSalesSource

BASE = "/v1/synapse/sales"
PERIODS = "start=2026-08-01&end=2026-08-31&compare_start=2026-07-01&compare_end=2026-07-31"
CUSTOMERS = [
    CustomerSales("A", "Acme", date(2026, 7, 10), Decimal("100.00"), 1, "INR"),
    CustomerSales("A", "Acme", date(2026, 8, 10), Decimal("10.00"), 1, "INR"),
    CustomerSales("B", "Beta", date(2026, 8, 10), Decimal("30.00"), 1, "INR"),
]
DAILY = [
    DailySales(date(2026, 7, 10), Decimal("100.00"), 1, "INR"),
    DailySales(date(2026, 8, 10), Decimal("40.00"), 2, "INR"),
]


def get(path: str, source: MockSalesSource, roles=("management",)):
    return make_client(source, list(roles)).get(f"{BASE}/{path}")


class TestCompareRoute:
    def test_by_customer_body(self):
        body = get(f"compare?{PERIODS}&by=customer", MockSalesSource(customers=CUSTOMERS)).json()
        [result] = body["comparisons"]
        assert (result["currency"], result["current"], result["previous"], result["change"], result["change_percent"]) == ("INR", "40.00", "100.00", "-60.00", "-60.00")
        assert [(r["key"], r["change"], r["share_of_change_percent"]) for r in result["rows"]] == [("A", "-90.00", "150.00"), ("B", "30.00", "-50.00")]

    def test_without_by_only_totals_and_rows_are_null(self):
        [result] = get(f"compare?{PERIODS}", MockSalesSource(DAILY)).json()["comparisons"]
        assert result["rows"] is None and result["change"] == "-60.00"

    def test_top_limits_the_rows_and_adds_other(self):
        [result] = get(f"compare?{PERIODS}&by=customer&top=1", MockSalesSource(customers=CUSTOMERS)).json()["comparisons"]
        assert [r["key"] for r in result["rows"]] == ["A", "other"]

    @pytest.mark.parametrize(
        "query",
        [
            "start=2026-08-31&end=2026-08-01&compare_start=2026-07-01&compare_end=2026-07-31",
            f"{PERIODS}&by=region",
            f"{PERIODS}&top=0",
            f"{PERIODS}&top=51",
            "start=2026-08-01&end=2026-08-31",
            "start=nope&end=2026-08-31&compare_start=2026-07-01&compare_end=2026-07-31",
            "start=2025-01-01&end=2026-08-31&compare_start=2026-07-01&compare_end=2026-07-31",
        ],
    )
    def test_invalid_queries_are_422(self, query):
        assert get(f"compare?{query}", MockSalesSource()).status_code == 422

    def test_invalid_query_has_the_code(self):
        assert get(f"compare?{PERIODS}&by=region", MockSalesSource()).json()["code"] == "INVALID_QUERY"


class TestMonthRoute:
    def test_body(self):
        [figure] = get("month?month=2026-08&trend=2", MockSalesSource(DAILY)).json()["figures"]
        assert figure["net_amount"] == "40.00"
        assert figure["order_count"] == 2
        assert figure["previous_change_percent"] == "-60.00"
        assert figure["complete"] is True
        assert [(t["month"], t["net_amount"]) for t in figure["trend"]] == [(7, "100.00"), (8, "40.00")]

    @pytest.mark.parametrize("query", ["month=2026-11", "month=2026-08&trend=25", "month=abc", ""])
    def test_invalid_queries_are_422(self, query):
        assert get(f"month?{query}", MockSalesSource(DAILY)).status_code == 422


class TestAccessAndAvailability:
    PATHS = [f"compare?{PERIODS}", "month?month=2026-08"]

    @pytest.mark.parametrize("path", PATHS)
    def test_no_cookie_is_401(self, path):
        assert make_client(MockSalesSource(DAILY)).get(f"{BASE}/{path}").status_code == 401

    @pytest.mark.parametrize("path", PATHS)
    @pytest.mark.parametrize("roles", [["sales"], []])
    def test_other_roles_are_403(self, path, roles):
        assert get(path, MockSalesSource(DAILY), roles).status_code == 403

    @pytest.mark.parametrize("path", PATHS)
    @pytest.mark.parametrize("role", ["management", "admin"])
    def test_management_and_admin_pass(self, path, role):
        assert get(path, MockSalesSource(DAILY), (role,)).status_code == 200

    @pytest.mark.parametrize("path", PATHS)
    def test_sap_down_is_503_with_nothing_partial(self, path):
        source = MockSalesSource(DAILY)
        source.fail()
        response = get(path, source)
        assert response.status_code == 503
        assert response.json() == {"code": "SAP_UNAVAILABLE"}


class TestCache:
    @pytest.mark.parametrize("path", [f"compare?{PERIODS}&by=customer", "month?month=2026-08"])
    def test_an_identical_call_is_served_from_the_cache(self, path):
        source = MockSalesSource(DAILY, CUSTOMERS)
        client, _ = make(source)
        client.get(f"{BASE}/{path}")
        calls = source.calls
        client.get(f"{BASE}/{path}")
        assert source.calls == calls

    def test_a_different_query_reads_again(self):
        source = MockSalesSource(DAILY, CUSTOMERS)
        client, _ = make(source)
        client.get(f"{BASE}/compare?{PERIODS}&by=customer")
        calls = source.calls
        client.get(f"{BASE}/compare?{PERIODS}&by=customer&top=3")
        assert source.calls > calls
