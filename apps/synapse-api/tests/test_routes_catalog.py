import pytest
from fastapi.testclient import TestClient
from test_routes_cache import Clock
from test_routes_totals import DAILY, SECRET, TODAY, make_client, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from synapse_api.application.sales_cache import SalesCache
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.settings import Settings

BASE = "/v1/synapse/catalog"


class TestAccess:
    @pytest.mark.parametrize("path", ["", "/sales-today/data"])
    def test_no_cookie_is_401(self, path):
        assert make_client(MockSalesSource(DAILY)).get(BASE + path).status_code == 401

    @pytest.mark.parametrize("roles", [["sales"], ["stores"]])
    def test_other_roles_are_403(self, roles):
        assert make_client(MockSalesSource(DAILY), roles).get(BASE).status_code == 403

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
        response = make_client(MockSalesSource(DAILY), ["management"]).get(f"{BASE}/sales-today/data")
        assert response.status_code == 200
        assert response.json()["value"] == 30.5
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
