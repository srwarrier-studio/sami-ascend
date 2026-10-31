from datetime import date

import pytest
from fastapi.testclient import TestClient
from test_routes_totals import SECRET, TODAY, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from synapse_api.application.sales_cache import SalesCache
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_record_source import MockRecordSource
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.settings import Settings

BASE = "/v1/synapse"
ROWS = {
    "purchase_delivery": [
        {"PurchaseOrder": "4500001207", "Material": "RAW-2002", "Supplier": "S1", "PromisedDeliveryDate": "2026-07-14", "ActualDeliveryDate": "2026-07-26", "DeliveryStatus": "D"},
    ],
    "contract": [{"SalesContract": "0040000127", "SoldToParty": "0000100001", "ValidFrom": "2025-07-13", "ValidTo": "2026-07-12"}],
}
WINDOW = "start=2026-07-01&end=2026-07-31"


class Clock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


def make(roles=("management",), source=None):
    source = source or MockRecordSource(ROWS)
    app = create_app(MockSalesSource(), Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY, SalesCache(300, Clock()), records=source)
    client = TestClient(app)
    if roles is not None:
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(list(roles)))
    return client, source


def get(path, roles=("management",), source=None):
    return make(roles, source)[0].get(f"{BASE}/{path}")


class TestRecords:
    def test_body_has_the_query_and_the_sap_fields_with_the_delay(self):
        body = get(f"records?type=purchase_delivery&key=RAW-2002&{WINDOW}").json()
        assert body["type"] == "purchase_delivery" and body["key_field"] == "Material" and body["key"] == "RAW-2002"
        assert (body["start"], body["end"]) == ("2026-07-01", "2026-07-31")
        [record] = body["records"]
        assert record["PurchaseOrder"] == "4500001207" and record["DeliveryStatus"] == "D" and record["delay_days"] == 12

    def test_key_field_is_chosen_by_the_caller(self):
        body = get(f"records?type=contract&key=0040000127&key_field=SalesContract&{WINDOW}").json()
        assert body["key_field"] == "SalesContract" and len(body["records"]) == 1

    def test_a_type_without_a_window_returns_null_dates(self):
        body = get("records?type=production_component&key=0001000417").json()
        assert (body["start"], body["end"], body["records"]) == (None, None, [])

    def test_an_empty_result_is_an_empty_list(self):
        assert get(f"records?type=contract&key=NOBODY&{WINDOW}").json()["records"] == []

    def test_an_unknown_type_is_404(self):
        response = get(f"records?type=invoice&key=X&{WINDOW}")
        assert (response.status_code, response.json()) == (404, {"code": "RECORD_TYPE_NOT_FOUND"})

    @pytest.mark.parametrize(
        "query",
        [
            f"type=contract&key=X'Y&{WINDOW}",
            f"type=contract&key=X&key_field=Nope&{WINDOW}",
            "type=contract&key=X",
            "type=contract&key=X&start=2026-07-31&end=2026-07-01",
            "type=contract&key=X&start=2025-01-01&end=2026-07-31",
            "type=contract",
        ],
    )
    def test_invalid_queries_are_422(self, query):
        assert get(f"records?{query}").status_code == 422


class TestTypes:
    def test_listing(self):
        types = {t["name"]: t for t in get("records/types").json()["types"]}
        assert list(types) == ["contract", "purchase_delivery", "production_order", "production_component"]
        assert types["purchase_delivery"] == {"name": "purchase_delivery", "key_fields": ["Material", "Supplier", "PurchaseOrder"], "takes_window": True, "has_delay_days": True}
        assert types["production_component"]["takes_window"] is False and types["contract"]["has_delay_days"] is False


class TestAccessAndAvailability:
    PATHS = [f"records?type=contract&key=X&{WINDOW}", "records/types"]

    @pytest.mark.parametrize("path", PATHS)
    def test_no_cookie_is_401(self, path):
        assert make(roles=None)[0].get(f"{BASE}/{path}").status_code == 401

    @pytest.mark.parametrize("path", PATHS)
    @pytest.mark.parametrize("roles", [["sales"], []])
    def test_other_roles_are_403(self, path, roles):
        assert get(path, roles).status_code == 403

    @pytest.mark.parametrize("path", PATHS)
    @pytest.mark.parametrize("role", ["management", "admin"])
    def test_management_and_admin_pass(self, path, role):
        assert get(path, (role,)).status_code == 200

    def test_sap_down_is_503_with_nothing_partial(self):
        source = MockRecordSource(ROWS)
        source.fail()
        response = get(f"records?type=contract&key=X&{WINDOW}", source=source)
        assert (response.status_code, response.json()) == (503, {"code": "SAP_UNAVAILABLE"})


class TestCache:
    def test_an_identical_call_is_served_from_the_cache_and_a_different_one_is_not(self):
        client, source = make()
        path = f"{BASE}/records?type=contract&key=0000100001&{WINDOW}"
        client.get(path)
        calls = source.calls
        client.get(path)
        assert source.calls == calls
        client.get(path.replace("0000100001", "0000100002"))
        assert source.calls > calls
