import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import jwt
import pytest

pytest.importorskip("butterfly")
pytest.importorskip("synapse_api")
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app
from butterfly.infrastructure.api.odata import DRIVERS_ROOT, ROOT
from intent_api.application.analysis.walk_graph import WalkGraph
from intent_api.domain.analysis.finding import Start, Window
from intent_api.infrastructure.graph_loader import load_graph
from intent_api.infrastructure.settings import GRAPH_FILE, Settings
from intent_api.infrastructure.synapse_data_source import SynapseDataSource
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.odata_reader import ODataReader
from synapse_api.infrastructure.registry_metric_source import RegistryMetricSource
from synapse_api.infrastructure.registry_record_source import RegistryRecordSource
from synapse_api.infrastructure.settings import Settings as SynapseSettings

TODAY = date(2026, 10, 31)
SECRET = "s" * 32
GRAPH = load_graph(GRAPH_FILE)
SCENARIOS_FOLDER = Path(__file__).resolve().parents[2] / "butterfly" / "scenarios"
USED = {"august-contract", "supplier-no-effect", "breakdown-shortfall", "customer-lost", "price-cut"}

AUGUST = Window.before(date(2026, 8, 1), date(2026, 8, 31))
JULY = Window.before(date(2026, 7, 1), date(2026, 7, 31))
JULY_TO_AUGUST = Window.before(date(2026, 7, 1), date(2026, 8, 31))


class Forward(httpx.BaseTransport):
    def __init__(self, client: TestClient):
        self.client = client

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        answer = self.client.get(str(request.url), headers=dict(request.headers))
        return httpx.Response(answer.status_code, json=answer.json())


def token() -> str:
    payload = {"sub": "u1", "sap_username": "SAP", "roles": ["management"], "companies": ["sabinsa", "neutraceuticals", "organica"], "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    return jwt.encode(payload, SECRET, algorithm="HS256")


def source_for(scenario: str) -> SynapseDataSource:
    butterfly = Forward(TestClient(build_default_app(TODAY, "story", scenario)))
    readers = {
        "sales": ODataReader(f"http://testserver{ROOT}", 10, butterfly),
        "drivers": ODataReader(f"http://testserver{DRIVERS_ROOT}", 10, butterfly),
    }
    app = create_app(
        MockSalesSource(), SynapseSettings(jwt_secret=SECRET, _env_file=None), lambda: TODAY,
        metrics=RegistryMetricSource(readers), records=RegistryRecordSource(readers),
    )
    return SynapseDataSource(Settings(synapse_url="http://testserver", _env_file=None), Forward(TestClient(app)))


def walk(scenario, mode, starts, window):
    return WalkGraph(GRAPH, source_for(scenario)).execute(mode, starts, window, token(), TODAY)


def names(path):
    return [(step.node, step.kind) for step in path]


class TestAugustContract:
    def test_harborline_has_no_valid_contract_from_13_july(self):
        [path] = walk("august-contract", "root_cause", [Start("Customer", "0000100001")], AUGUST).paths
        [step] = path
        assert names(path) == [("Contract", "coverage_gap")]
        assert (step.numbers["days_uncovered"], step.at, [r["SalesContract"] for r in step.rows]) == (50, date(2026, 7, 13), ["0040000127"])

    def test_piperine_leads_to_the_late_production_order_and_behind_it_the_late_delivery(self):
        [path] = walk("august-contract", "root_cause", [Start("Product", "RM-1002")], AUGUST).paths
        [order, delivery] = path
        assert names(path) == [("ProductionOrder", "later_than"), ("PurchaseDelivery", "later_than")]
        assert (order.rows[0]["ProductionOrder"], order.numbers["days_late"], order.rows[0]["DelayReason"]) == ("0001000417", 14, "MATERIAL_SHORTAGE")
        assert (delivery.rows[0]["PurchaseOrder"], delivery.numbers["days_late"], delivery.at) == ("4500001207", 12, date(2026, 7, 14))

    def test_the_may_decoys_are_outside_the_lookback_and_not_reported(self):
        result = walk("august-contract", "root_cause", [Start("Product", "RM-1005"), Start("Product", "RM-1003")], AUGUST)
        assert result.paths == []

    def test_they_are_found_when_the_window_is_may(self):
        window = Window.before(date(2026, 5, 1), date(2026, 5, 31))
        [path] = walk("august-contract", "root_cause", [Start("Product", "RM-1005")], window).paths
        assert (path[0].rows[0]["DelayReason"], path[0].numbers["days_late"]) == ("MACHINE_BREAKDOWN", 6)

    def test_impact_of_the_late_delivery_reaches_production_and_the_sales_that_fell(self):
        [path] = walk("august-contract", "impact", [Start("PurchaseDelivery", "4500001207", "PurchaseOrder")], JULY).paths
        assert names(path) == [("PurchaseDelivery", "later_than"), ("ProductionOrder", "later_than"), ("Product", "value_changed")]
        assert path[1].rows[0]["ProductionOrder"] == "0001000417" and path[2].keys == ("RM-1002",)
        assert path[2].numbers["change_percent"] < 0

    def test_dependency_lists_what_feeds_steel_plate(self):
        result = walk("august-contract", "dependency", [Start("Product", "RM-1002")], AUGUST)
        related = {(r.node, r.key) for r in result.related}
        assert ("PurchaseDelivery", "RAW-2002") in related and ("ProductionOrder", "RM-1002") in related and result.paths == []


class TestSupplierNoEffect:
    def test_impact_stops_at_production_because_sales_did_not_move(self):
        [path] = walk("supplier-no-effect", "impact", [Start("PurchaseDelivery", "4500001207", "PurchaseOrder")], JULY).paths
        assert names(path) == [("PurchaseDelivery", "later_than"), ("ProductionOrder", "later_than")]


class TestBreakdownShortfall:
    def test_bearing_leads_to_the_breakdown_order_and_to_no_delivery(self):
        [path] = walk("breakdown-shortfall", "root_cause", [Start("Product", "RM-1005")], JULY_TO_AUGUST).paths
        [order] = path
        assert (order.rows[0]["ProductionOrder"], order.rows[0]["DelayReason"], order.numbers["days_late"]) == ("0001000420", "MACHINE_BREAKDOWN", 10)


class TestNothingBehindTheMover:
    def test_a_lost_customer_with_a_valid_contract_has_no_cause(self):
        assert walk("customer-lost", "root_cause", [Start("Customer", "0000100005")], AUGUST).paths == []

    def test_a_price_cut_has_nothing_behind_it(self):
        assert walk("price-cut", "root_cause", [Start("Product", "RM-1001")], AUGUST).paths == []


class TestHeldBackScenariosStayUnread:
    def test_none_of_the_scenarios_used_here_is_held_back(self):
        held_back = {path.stem for path in SCENARIOS_FOLDER.glob("*.json") if json.loads(path.read_text())["holdout"]}
        assert held_back and not USED & held_back
