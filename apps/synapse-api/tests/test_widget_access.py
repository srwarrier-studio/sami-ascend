import pytest
from test_routes_totals import DAILY, TODAY, SECRET, make_client

from synapse_api.domain.entities.widget_access import WidgetAccess
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.settings import Settings
from synapse_api.infrastructure.widget_access_loader import load_widget_access

BASE = "/v1/synapse/catalog"


def categories(client) -> set[str]:
    return {entry["category"] for entry in client.get(BASE).json()["entries"]}


def only_sales_row(roles: list[str]):
    from fastapi.testclient import TestClient
    from test_routes_totals import token_with
    from token_verification import Role
    from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

    app = create_app(MockSalesSource(DAILY), Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY, access=WidgetAccess({name: frozenset({Role.SALES}) for name in ("Sales", "Exports", "Finance", "Purchase", "Inventory", "Production")}))
    client = TestClient(app)
    client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(roles))
    return client


class TestCatalogByRole:
    @pytest.mark.parametrize(
        "roles, expected",
        [
            (["production"], {"Production"}),
            (["accounts"], {"Finance"}),
            (["stores"], {"Inventory", "Production"}),
            (["production", "accounts"], {"Production", "Finance"}),
            (["sales"], {"Sales", "Exports"}),
        ],
    )
    def test_a_user_sees_only_the_categories_their_roles_allow(self, roles, expected):
        assert categories(make_client(MockSalesSource(DAILY), roles)) == expected

    @pytest.mark.parametrize("roles", [["management"], ["admin"]])
    def test_management_and_admin_see_every_category(self, roles):
        assert categories(make_client(MockSalesSource(DAILY), roles)) == {"Sales", "Exports", "Finance", "Purchase", "Inventory", "Production"}


class TestDataByRole:
    def test_a_hidden_widget_is_403(self):
        response = make_client(MockSalesSource(DAILY), ["production"]).get(f"{BASE}/fin-collections/data")
        assert response.status_code == 403
        assert response.json() == {"code": "WIDGET_NOT_ALLOWED"}

    def test_an_allowed_widget_is_served(self):
        assert make_client(MockSalesSource(DAILY), ["accounts"]).get(f"{BASE}/fin-collections/data").status_code == 200

    def test_an_unknown_widget_is_404_not_403(self):
        assert make_client(MockSalesSource(DAILY), ["production"]).get(f"{BASE}/nope/data").status_code == 404


class TestEntryGate:
    def test_a_role_in_no_row_is_403(self):
        client = make_client(MockSalesSource(DAILY), ["quality"])
        assert client.get(BASE).status_code == 200
        assert only_sales_row(["quality"]).get(BASE).status_code == 403

    def test_metrics_stay_management_only(self):
        assert make_client(MockSalesSource(DAILY), ["production"]).get("/v1/synapse/sales/today").status_code == 403


class TestSummaryByRole:
    def test_ids_the_caller_cannot_see_are_ignored(self):
        client = make_client(MockSalesSource(DAILY), ["accounts"])
        body = client.get("/v1/synapse/summary?widgets=sales-today,fin-collections").json()
        assert all("Sales" not in sentence for sentence in body["sentences"])


class TestStartup:
    def test_a_category_without_a_row_stops_the_app(self):
        with pytest.raises(ValueError, match="no row for"):
            create_app(MockSalesSource(DAILY), Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY, access=WidgetAccess({}))

    def test_the_shipped_table_loads(self):
        assert load_widget_access(Settings(_env_file=None).widget_access_path).allows([], "Sales") is False
