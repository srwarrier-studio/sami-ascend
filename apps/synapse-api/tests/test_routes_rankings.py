from datetime import date
from decimal import Decimal

import pytest
from test_routes_totals import make_client

from synapse_api.domain.entities.sales import CustomerSales, DailySales, HighValueOrder, MaterialSales
from synapse_api.infrastructure.mock_sales_source import MockSalesSource

BASE = "/v1/synapse/sales"

CUSTOMERS = [
    CustomerSales("C1", "Acme", date(2026, 10, 2), Decimal("100.00"), 1, "INR"),
    CustomerSales("C1", "Acme", date(2026, 10, 20), Decimal("50.00"), 2, "INR"),
    CustomerSales("C2", "Beta", date(2026, 10, 5), Decimal("120.00"), 1, "INR"),
]
MATERIALS = [
    MaterialSales("M1", "Bolt", date(2026, 10, 2), Decimal("10.000"), "EA", Decimal("40.00"), "INR"),
    MaterialSales("M1", "Bolt", date(2026, 10, 9), Decimal("5.000"), "EA", Decimal("20.00"), "INR"),
    MaterialSales("M2", "Nut", date(2026, 10, 9), Decimal("1.000"), "KG", Decimal("90.00"), "INR"),
]
ORDERS = [
    HighValueOrder("0000012001", "Acme", date(2026, 10, 20), Decimal("250000.00"), "INR", "A"),
    HighValueOrder("0000012002", "Beta", date(2026, 10, 25), Decimal("150000.00"), "INR", "B"),
    HighValueOrder("0000012003", "Gamma", date(2026, 10, 26), Decimal("500.00"), "INR", "A"),
]
DAILY = [
    DailySales(date(2026, 9, 3), Decimal("10.00"), 1, "INR"),
    DailySales(date(2026, 10, 3), Decimal("20.00"), 1, "INR"),
]


def get(path: str, source: MockSalesSource, roles=("management",)):
    return make_client(source, list(roles)).get(f"{BASE}/{path}")


class TestMonthOnMonthRoute:
    def test_body_lists_months_oldest_first(self):
        body = get("month-on-month?months=2", MockSalesSource(DAILY)).json()
        assert body == {
            "months": [
                {"year": 2026, "month": 9, "net_amount": "10.00", "currency": "INR"},
                {"year": 2026, "month": 10, "net_amount": "20.00", "currency": "INR"},
            ]
        }

    def test_default_is_twelve_months(self):
        body = get("month-on-month", MockSalesSource(DAILY)).json()
        assert len(body["months"]) == 12


class TestTopCustomersRoute:
    def test_body_ranks_by_net_amount(self):
        body = get("top-customers", MockSalesSource(customers=CUSTOMERS)).json()
        assert body == {
            "customers": [
                {"customer": "C1", "name": "Acme", "net_amount": "150.00", "order_count": 3, "currency": "INR"},
                {"customer": "C2", "name": "Beta", "net_amount": "120.00", "order_count": 1, "currency": "INR"},
            ]
        }

    def test_top_cuts_the_list(self):
        body = get("top-customers?top=1", MockSalesSource(customers=CUSTOMERS)).json()
        assert [c["customer"] for c in body["customers"]] == ["C1"]


class TestTopMaterialsRoute:
    def test_body_ranks_by_net_amount(self):
        body = get("top-materials", MockSalesSource(materials=MATERIALS)).json()
        assert body["materials"][0] == {
            "material": "M2",
            "description": "Nut",
            "quantity": "1.000",
            "unit": "KG",
            "net_amount": "90.00",
            "currency": "INR",
        }
        assert body["materials"][1]["quantity"] == "15.000"

    def test_top_cuts_the_list(self):
        body = get("top-materials?top=1", MockSalesSource(materials=MATERIALS)).json()
        assert len(body["materials"]) == 1


class TestHighValueOrdersRoute:
    def test_default_minimum_is_one_lakh_newest_first(self):
        body = get("high-value-orders", MockSalesSource(orders=ORDERS)).json()
        assert [o["order"] for o in body["orders"]] == ["0000012002", "0000012001"]
        assert body["orders"][0] == {
            "order": "0000012002",
            "customer_name": "Beta",
            "order_date": "2026-10-25",
            "net_amount": "150000.00",
            "currency": "INR",
            "status": "B",
        }

    def test_minimum_and_top_are_passed_through(self):
        body = get("high-value-orders?minimum=200000&top=1", MockSalesSource(orders=ORDERS)).json()
        assert [o["order"] for o in body["orders"]] == ["0000012001"]


class TestInvalidInput:
    @pytest.mark.parametrize(
        "path",
        [
            "top-customers?top=0",
            "top-customers?top=51",
            "top-materials?top=0",
            "top-materials?top=51",
            "high-value-orders?top=0",
            "high-value-orders?top=51",
            "month-on-month?months=0",
            "month-on-month?months=25",
        ],
    )
    def test_out_of_range_is_422_invalid_query(self, path):
        response = get(path, MockSalesSource())
        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_QUERY"

    @pytest.mark.parametrize("path", ["top-customers?top=abc", "high-value-orders?minimum=abc"])
    def test_not_a_number_is_422(self, path):
        assert get(path, MockSalesSource()).status_code == 422

    def test_invalid_top_does_not_call_the_source(self):
        source = MockSalesSource()
        source.fail()
        assert get("top-customers?top=0", source).status_code == 422


class TestAccessAndSapDown:
    @pytest.mark.parametrize("path", ["month-on-month", "top-customers", "top-materials", "high-value-orders"])
    def test_other_roles_are_403(self, path):
        assert get(path, MockSalesSource(), roles=("sales",)).status_code == 403

    @pytest.mark.parametrize("path", ["month-on-month", "top-customers", "top-materials", "high-value-orders"])
    def test_failing_source_is_503(self, path):
        source = MockSalesSource()
        source.fail()
        response = get(path, source)
        assert response.status_code == 503
        assert response.json() == {"code": "SAP_UNAVAILABLE"}
