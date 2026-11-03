from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from test_routes_cache import Clock
from test_routes_totals import DAILY, SECRET, TODAY, make_client, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from synapse_api.application.sales_cache import SalesCache
from synapse_api.domain.entities.sales import CustomerSales
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.settings import Settings

BASE = "/v1/synapse/catalog"


class TestAccess:
    @pytest.mark.parametrize("path", ["", "/sales-today/data"])
    def test_no_cookie_is_401(self, path):
        assert make_client(MockSalesSource(DAILY)).get(BASE + path).status_code == 401

    @pytest.mark.parametrize("roles", [["management"], ["admin"]])
    def test_management_and_admin_pass(self, roles):
        assert make_client(MockSalesSource(DAILY), roles).get(BASE).status_code == 200


class TestCatalog:
    def test_lists_sales_and_library_entries(self):
        body = make_client(MockSalesSource(DAILY), ["management"]).get(BASE).json()
        ids = [e["id"] for e in body["entries"]]
        assert len(ids) == 50
        assert ids[0] == "sales-today" and "inv-low" in ids
        assert body["entries"][0] == {
            "id": "sales-today",
            "title": "Sales today",
            "description": "Net sales invoiced today against yesterday.",
            "category": "Sales",
            "widget": "KpiCard",
        }

    def test_serves_a_sales_widgets_props(self):
        response = make_client(MockSalesSource(DAILY), ["management"]).get(f"{BASE}/sales-today/data?currency=INR")
        assert response.status_code == 200
        assert response.json()["value"] == 30.5
        assert response.json()["currency"] == "INR"
        assert response.json()["valueFormat"] == "currency"

    def test_serves_a_library_widgets_props(self):
        assert make_client(MockSalesSource(DAILY), ["management"]).get(f"{BASE}/inv-low/data").json()["value"] == 14

    def test_unknown_id_is_404_in_the_error_shape(self):
        response = make_client(MockSalesSource(DAILY), ["management"]).get(f"{BASE}/nope/data")
        assert (response.status_code, response.json()) == (404, {"code": "CATALOG_ENTRY_NOT_FOUND"})


class TestCache:
    def test_a_second_call_inside_the_window_does_not_read_the_source_again(self):
        source = MockSalesSource(DAILY)
        clock = Clock()
        app = create_app(source, Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY, SalesCache(300, clock))
        client = TestClient(app)
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"]))
        client.get(f"{BASE}/top-customers/data")
        calls = source.calls
        client.get(f"{BASE}/top-customers/data")
        assert source.calls == calls
        clock.now = 301
        client.get(f"{BASE}/top-customers/data")
        assert source.calls > calls


class TestCurrency:
    def widget(self, query: str = "", daily=None):
        return make_client(MockSalesSource(daily or DAILY), ["management"]).get(f"{BASE}/sales-today/data{query}")

    def test_the_default_currency_is_rupees_and_the_widget_names_it(self):
        assert self.widget().json()["currency"] == "INR"

    def test_a_widget_shows_only_the_asked_currency(self):
        from test_sales_widgets import day

        daily = [day(TODAY, "30.5", currency="INR"), day(TODAY, "7.25", currency="USD")]
        assert self.widget("?currency=USD", daily).json()["value"] == 7.25
        assert self.widget("?currency=inr", daily).json()["value"] == 30.5

    @pytest.mark.parametrize("bad", ["US", "USDX", "12$"])
    def test_a_bad_currency_is_422(self, bad):
        assert self.widget(f"?currency={bad}").status_code == 422

    def test_each_currency_is_cached_on_its_own(self):
        from test_sales_widgets import day

        source = MockSalesSource([day(TODAY, "30.5", currency="INR"), day(TODAY, "7.25", currency="USD")])
        http = make_client(source, ["management"])
        assert [http.get(f"{BASE}/sales-today/data?currency={c}").json()["value"] for c in ("USD", "INR", "USD")] == [7.25, 30.5, 7.25]


class TestTop:
    def rows(self, query: str):
        from test_sales_widgets import day  # noqa: F401

        customers = [CustomerSales(str(n), f"Customer {n}", TODAY, Decimal(100 - n), 1, "INR") for n in range(1, 9)]
        return make_client(MockSalesSource(DAILY, customers=customers), ["management"]).get(f"{BASE}/top-customers/data{query}")

    def test_a_ranking_has_five_rows_unless_asked_for_more(self):
        assert len(self.rows("").json()["items"]) == 5
        assert len(self.rows("?top=8").json()["items"]) == 8

    @pytest.mark.parametrize("bad", ["0", "21", "x"])
    def test_a_bad_top_is_422(self, bad):
        assert self.rows(f"?top={bad}").status_code == 422


class TestRealSourcesReplaceTheMockLibrary:
    def client(self):
        from test_routes_totals import SECRET, TODAY as DAY, token_with
        from synapse_api.infrastructure.mock_purchase_source import MockPurchaseSource
        from synapse_api.infrastructure.mock_receivables_source import MockReceivablesSource

        app = create_app(MockSalesSource(), Settings(jwt_secret=SECRET, _env_file=None), lambda: DAY, purchases=MockPurchaseSource(), receivables=MockReceivablesSource())
        client = TestClient(app)
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"]))
        return client

    def test_each_id_is_listed_once_and_the_rest_of_the_library_stays(self):
        ids = [e["id"] for e in self.client().get(BASE).json()["entries"]]
        assert len(ids) == len(set(ids)) == 50
        assert {"pur-spend", "fin-receivables", "pur-categories", "exp-revenue"} <= set(ids)

    def test_a_replaced_id_is_served_by_the_real_source(self):
        body = self.client().get(f"{BASE}/pur-spend/data").json()
        assert body["measure"] == "purchases" and body["value"] == 0.0 and "period" in body

    def test_an_id_with_no_real_source_still_comes_from_the_library(self):
        assert self.client().get(f"{BASE}/exp-revenue/data").json()["title"] == "Export revenue"
