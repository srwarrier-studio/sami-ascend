from datetime import date

import httpx
import pytest

pytest.importorskip("butterfly")
from fastapi.testclient import TestClient
from test_routes_totals import SECRET, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from butterfly.entrypoint.app import build_default_app
from synapse_api.application.read_records import ReadRecords
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.odata_reader import ODataReader
from synapse_api.infrastructure.registry_loader import load_registry
from synapse_api.infrastructure.registry_record_source import RegistryRecordSource
from synapse_api.infrastructure.settings import REGISTRY_PATH, Settings

TODAY = date(2026, 10, 31)
REGISTRY = load_registry(REGISTRY_PATH)
ROOT = "http://testserver/sap/opu/odata4/sap/zui_drivers_o4/srvd_a2x/sap/zdrivers/0001/"


class InProcess(httpx.BaseTransport):
    def __init__(self, scenario: str):
        self.butterfly = TestClient(build_default_app(TODAY, "story", scenario))

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        answer = self.butterfly.get(str(request.url))
        return httpx.Response(answer.status_code, json=answer.json())


def record_source(scenario: str) -> RegistryRecordSource:
    return RegistryRecordSource({"drivers": ODataReader(ROOT, 10, InProcess(scenario))})


def read(scenario, type_name, key, start=None, end=None, key_field=None):
    return ReadRecords(record_source(scenario), REGISTRY).execute(type_name, key, key_field, start, end, TODAY)[1]


JULY = (date(2026, 7, 1), date(2026, 7, 31))
JULY_TO_AUGUST = (date(2026, 7, 1), date(2026, 8, 31))


class TestAugustContract:
    def test_the_contract_that_ended_is_found_and_the_renewal_is_not(self):
        rows = read("august-contract", "contract", "0000100001", *JULY_TO_AUGUST)
        assert [r["SalesContract"] for r in rows] == ["0040000127"]

    def test_the_renewal_is_found_in_september(self):
        rows = read("august-contract", "contract", "0000100001", date(2026, 9, 1), date(2026, 9, 30))
        assert [r["SalesContract"] for r in rows] == ["0040000163"]

    def test_the_late_steel_coil_delivery_has_twelve_days_of_delay(self):
        rows = read("august-contract", "purchase_delivery", "RAW-2002", *JULY)
        late = next(r for r in rows if r["PurchaseOrder"] == "4500001207")
        assert (late["PromisedDeliveryDate"], late["ActualDeliveryDate"], late["delay_days"]) == ("2026-07-14", "2026-07-26", 12)

    def test_the_steel_plate_order_is_fourteen_days_late_for_a_shortage(self):
        rows = read("august-contract", "production_order", "RM-1002", *JULY_TO_AUGUST)
        late = next(r for r in rows if r["ProductionOrder"] == "0001000417")
        assert (late["delay_days"], late["DelayReason"]) == (14, "MATERIAL_SHORTAGE")

    def test_its_component_is_the_steel_coil(self):
        [component] = read("august-contract", "production_component", "0001000417")
        assert component["Material"] == "RAW-2002"

    def test_the_orders_that_use_steel_coil_are_found_from_the_material(self):
        rows = read("august-contract", "production_component", "RAW-2002", key_field="Material")
        assert "0001000417" in {r["ProductionOrder"] for r in rows}

    def test_the_decoys_are_real_records_too(self):
        rows = read("august-contract", "production_order", "RM-1005", date(2026, 5, 1), date(2026, 5, 31))
        assert any(r["DelayReason"] == "MACHINE_BREAKDOWN" and r["delay_days"] == 6 for r in rows)


class TestBreakdownShortfall:
    def test_the_bearing_order_is_late_because_of_the_breakdown(self):
        rows = read("breakdown-shortfall", "production_order", "RM-1005", *JULY)
        broken = [r for r in rows if r["DelayReason"] == "MACHINE_BREAKDOWN"]
        assert len(broken) == 1 and broken[0]["delay_days"] == 10


class TestThroughTheRoute:
    def test_the_route_returns_the_same_records_as_butterfly(self):
        settings = Settings(jwt_secret=SECRET, _env_file=None)
        app = create_app(MockSalesSource(), settings, lambda: TODAY, records=record_source("august-contract"))
        client = TestClient(app)
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"]))
        body = client.get("/v1/synapse/records?type=purchase_delivery&key=RAW-2002&start=2026-07-01&end=2026-07-31").json()
        assert any(r["PurchaseOrder"] == "4500001207" and r["delay_days"] == 12 for r in body["records"])
