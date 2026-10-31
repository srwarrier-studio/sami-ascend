from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from test_routes_totals import SECRET, TODAY, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from synapse_api.application.sales_cache import SalesCache
from synapse_api.domain.entities.metric_row import MetricRow
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_metric_source import MockMetricSource
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.settings import Settings

BASE = "/v1/synapse"
PERIODS = "start=2026-08-01&end=2026-08-31&compare_start=2026-07-01&compare_end=2026-07-31"


def row(key, name, d, amount, quantity=None, count=1):
    return MetricRow(key, name, d, Decimal(amount), "INR", Decimal(quantity) if quantity else None, "EA" if quantity else None, count)


def metric_source() -> MockMetricSource:
    return MockMetricSource({
        ("sales", "customer"): [
            row("A", "Acme", date(2026, 7, 10), "100.00"),
            row("A", "Acme", date(2026, 8, 10), "10.00"),
            row("B", "Beta", date(2026, 8, 10), "30.00"),
        ],
        ("sales", "material"): [row("M", "Bolt", date(2026, 7, 10), "100.00", "10.000"), row("M", "Bolt", date(2026, 8, 10), "85.00", "10.000")],
        ("sales", "day"): [row(None, "", date(2026, 7, 10), "100.00", count=1), row(None, "", date(2026, 8, 10), "40.00", count=2)],
    })


class Clock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


def make(source=None, roles=("management",), seconds=300):
    source = source or metric_source()
    app = create_app(MockSalesSource(), Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY, SalesCache(seconds, Clock()), metrics=source)
    client = TestClient(app)
    if roles is not None:
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(list(roles)))
    return client, source


def get(path: str, source=None, roles=("management",)):
    return make(source, roles)[0].get(f"{BASE}/{path}")


class TestListing:
    def test_metrics_with_their_dimensions_and_whether_they_split_price(self):
        body = get("metrics").json()
        by_name = {m["name"]: m for m in body["metrics"]}
        assert list(by_name) == ["sales", "purchases"]
        assert by_name["sales"] == {
            "name": "sales",
            "label": "Sales",
            "dimensions": [
                {"name": "customer", "splits_volume_and_price": False},
                {"name": "material", "splits_volume_and_price": True},
            ],
        }
        assert [d["name"] for d in by_name["purchases"]["dimensions"]] == ["supplier", "material"]


class TestCompareRoute:
    def test_by_customer_body(self):
        [result] = get(f"metrics/sales/compare?{PERIODS}&by=customer").json()["comparisons"]
        assert (result["currency"], result["current"], result["previous"], result["change"], result["change_percent"]) == ("INR", "40.00", "100.00", "-60.00", "-60.00")
        assert [(r["key"], r["change"], r["share_of_change_percent"]) for r in result["rows"]] == [("A", "-90.00", "150.00"), ("B", "30.00", "-50.00")]

    def test_by_material_has_the_price_split(self):
        [result] = get(f"metrics/sales/compare?{PERIODS}&by=material").json()["comparisons"]
        item = result["rows"][0]
        assert (item["price_effect"], item["volume_effect"], item["price_previous"], item["price_current"]) == ("-15.00", "0.00", "10.0000", "8.5000")

    def test_without_by_only_totals_and_rows_are_null(self):
        [result] = get(f"metrics/sales/compare?{PERIODS}").json()["comparisons"]
        assert result["rows"] is None and result["change"] == "-60.00"

    def test_top_limits_the_rows_and_adds_other(self):
        [result] = get(f"metrics/sales/compare?{PERIODS}&by=customer&top=1").json()["comparisons"]
        assert [r["key"] for r in result["rows"]] == ["A", "other"]

    def test_an_unknown_metric_is_404(self):
        response = get(f"metrics/weather/compare?{PERIODS}")
        assert (response.status_code, response.json()) == (404, {"code": "METRIC_NOT_FOUND"})

    @pytest.mark.parametrize(
        "query",
        [
            "start=2026-08-31&end=2026-08-01&compare_start=2026-07-01&compare_end=2026-07-31",
            f"{PERIODS}&by=region",
            f"{PERIODS}&by=day",
            f"{PERIODS}&top=0",
            f"{PERIODS}&top=51",
            "start=2026-08-01&end=2026-08-31",
            "start=nope&end=2026-08-31&compare_start=2026-07-01&compare_end=2026-07-31",
            "start=2025-01-01&end=2026-08-31&compare_start=2026-07-01&compare_end=2026-07-31",
        ],
    )
    def test_invalid_queries_are_422(self, query):
        assert get(f"metrics/sales/compare?{query}").status_code == 422

    def test_invalid_query_has_the_code(self):
        assert get(f"metrics/sales/compare?{PERIODS}&by=region").json()["code"] == "INVALID_QUERY"


class TestMonthRoute:
    def test_body(self):
        [figure] = get("metrics/sales/month?month=2026-08&trend=2").json()["figures"]
        assert figure["net_amount"] == "40.00"
        assert figure["order_count"] == 2
        assert figure["previous_change_percent"] == "-60.00"
        assert figure["complete"] is True
        assert [(t["month"], t["net_amount"]) for t in figure["trend"]] == [(7, "100.00"), (8, "40.00")]

    @pytest.mark.parametrize("query", ["month=2026-11", "month=2026-08&trend=25", "month=abc", ""])
    def test_invalid_queries_are_422(self, query):
        assert get(f"metrics/sales/month?{query}").status_code == 422

    def test_an_unknown_metric_is_404(self):
        assert get("metrics/weather/month?month=2026-08").status_code == 404


class TestAccessAndAvailability:
    PATHS = ["metrics", f"metrics/sales/compare?{PERIODS}", "metrics/sales/month?month=2026-08"]

    @pytest.mark.parametrize("path", PATHS)
    def test_no_cookie_is_401(self, path):
        assert make(roles=None)[0].get(f"{BASE}/{path}").status_code == 401

    @pytest.mark.parametrize("path", PATHS)
    @pytest.mark.parametrize("roles", [["sales"], []])
    def test_other_roles_are_403(self, path, roles):
        assert get(path, roles=roles).status_code == 403

    @pytest.mark.parametrize("path", PATHS)
    @pytest.mark.parametrize("role", ["management", "admin"])
    def test_management_and_admin_pass(self, path, role):
        assert get(path, roles=(role,)).status_code == 200

    @pytest.mark.parametrize("path", PATHS[1:])
    def test_sap_down_is_503_with_nothing_partial(self, path):
        source = metric_source()
        source.fail()
        response = get(path, source)
        assert (response.status_code, response.json()) == (503, {"code": "SAP_UNAVAILABLE"})

    @pytest.mark.parametrize("path", ["sales/compare?" + PERIODS, "sales/month?month=2026-08"])
    def test_the_old_sales_only_routes_are_gone(self, path):
        assert get(path).status_code == 404


class TestCache:
    @pytest.mark.parametrize("path", [f"metrics/sales/compare?{PERIODS}&by=customer", "metrics/sales/month?month=2026-08"])
    def test_an_identical_call_is_served_from_the_cache(self, path):
        client, source = make()
        client.get(f"{BASE}/{path}")
        calls = source.calls
        client.get(f"{BASE}/{path}")
        assert source.calls == calls

    def test_a_different_query_reads_again(self):
        client, source = make()
        client.get(f"{BASE}/metrics/sales/compare?{PERIODS}&by=customer")
        calls = source.calls
        client.get(f"{BASE}/metrics/sales/compare?{PERIODS}&by=customer&top=3")
        assert source.calls > calls

    def test_an_app_without_a_metric_source_has_no_metric_routes(self):
        app = create_app(MockSalesSource(), Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY)
        client = TestClient(app)
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"]))
        assert client.get(f"{BASE}/metrics").status_code == 404
