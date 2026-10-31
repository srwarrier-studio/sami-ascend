import json
import re
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app
from butterfly.infrastructure.api.odata import DRIVERS_ROOT, ROOT
from butterfly.infrastructure.memory.scenarios import AUGUST_CONTRACT, SCENARIOS, find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from contract_helpers import same_shape
from test_contract import ITEM_TABLE, ORDER_TABLE, check_rows

TODAY = date(2026, 10, 31)
NAMES = [s.name for s in SCENARIOS]
DRIVERS_CONTRACT = (Path(__file__).resolve().parents[3] / "docs/sap/drivers-contract.md").read_text()
DRIVER_EXAMPLES = re.findall(r"```\nGET \{root\}([^\n]+)\n```\n\n```json\n(.*?)\n```", DRIVERS_CONTRACT, re.DOTALL)
TRUTHS = {p.stem: json.loads(p.read_text()) for p in (Path(__file__).resolve().parent.parent / "scenarios").glob("*.json")}


def client_for(name: str) -> TestClient:
    return TestClient(build_default_app(TODAY, "story", name))


class TestChoosingTheScenario:
    def test_the_default_is_august_contract(self):
        default = TestClient(build_default_app(TODAY, "story"))
        chosen = client_for("august-contract")
        query = ROOT + "SalesOrder?$top=50&$skip=900"
        assert default.get(query).json() == chosen.get(query).json()

    def test_the_environment_variable_chooses_the_scenario(self, monkeypatch):
        monkeypatch.setenv("BUTTERFLY_SCENARIO", "customer-lost")
        query = ROOT + "SalesOrder?$filter=SoldToParty eq '0000100005' and OrderDate ge 2026-08-10&$count=true&$top=1"
        assert TestClient(build_default_app(TODAY, "story")).get(query).json()["@odata.count"] == 0
        assert client_for("august-contract").get(query).json()["@odata.count"] > 0

    def test_an_unknown_scenario_stops_with_the_list_of_names(self):
        with pytest.raises(SystemExit) as stopped:
            build_default_app(TODAY, "story", "nonsense")
        assert "nonsense" in str(stopped.value)
        assert "price-cut" in str(stopped.value)

    def test_the_small_seed_ignores_the_scenario(self):
        assert TestClient(build_default_app(TODAY, "small", "nonsense")).get(ROOT + "SalesOrder?$top=1&$count=true").json()["@odata.count"] == 30


class TestContractsHoldForEveryScenario:
    @pytest.mark.parametrize("name", NAMES)
    def test_every_order_and_item_matches_the_sales_field_tables(self, name):
        rows = client_for(name).get(ROOT + "SalesOrder", params={"$expand": "_Item", "$top": 150}).json()["value"]
        check_rows([{k: v for k, v in row.items() if k != "_Item"} for row in rows], ORDER_TABLE)
        check_rows([item for row in rows for item in row["_Item"]], ITEM_TABLE)

    @pytest.mark.parametrize("name", NAMES)
    @pytest.mark.parametrize("request_text,response_text", DRIVER_EXAMPLES, ids=[e[0][:40] for e in DRIVER_EXAMPLES])
    def test_the_drivers_responses_have_the_shape_of_the_contract_examples(self, name, request_text, response_text):
        response = client_for(name).get(DRIVERS_ROOT + request_text)
        assert response.status_code == 200
        same_shape(response.json(), json.loads(response_text))

    @pytest.mark.parametrize("name", NAMES)
    def test_the_summaries_exclude_cancelled_orders_and_add_up_to_the_orders(self, name):
        seed = build_story_seed(TODAY, find_scenario(name))
        live = sum(o.total_net_amount for o in seed.orders if o.overall_status != "X")
        client, rows = client_for(name), []
        while page := client.get(ROOT + "SalesSummaryByCustomer", params={"$skip": len(rows)}).json()["value"]:
            rows += page
        assert sum(float(r["TotalNetAmount"]) for r in rows) == pytest.approx(float(live), rel=1e-9)


class TestTheScenarioListAgrees:
    def test_names_are_unique(self):
        assert len(set(NAMES)) == len(NAMES)

    def test_there_is_one_ground_truth_file_per_scenario(self):
        assert sorted(TRUTHS) == sorted(NAMES)

    def test_each_file_names_its_scenario_and_agrees_on_the_held_back_flag(self):
        for scenario in SCENARIOS:
            assert TRUTHS[scenario.name]["scenario"] == scenario.name
            assert TRUTHS[scenario.name]["holdout"] == scenario.holdout

    def test_exactly_four_scenarios_are_held_back(self):
        assert sorted(s.name for s in SCENARIOS if s.holdout) == ["cancellations", "double-cause", "supplier-switch", "two-causes"]

    def test_august_contract_is_the_default_scenario(self):
        assert SCENARIOS[0] is AUGUST_CONTRACT


class TestEveryTruthNamesItsMetric:
    def test_the_metric_is_sales_or_purchases_and_matches_the_events(self):
        for name, truth in TRUTHS.items():
            assert truth["metric"] in ("sales", "purchases"), name
        assert {n for n, t in TRUTHS.items() if t["metric"] == "purchases"} == {
            "purchase-price-rise", "stock-up", "demand-surge", "quiet-purchases", "supplier-switch", "double-cause"
        }


class TestSalesScenariosLeavePurchasesNormal:
    @pytest.mark.parametrize("name", [n for n in NAMES if TRUTHS[n]["metric"] == "sales"])
    def test_no_month_of_purchases_is_far_from_the_normal_level(self, name):
        seed = build_story_seed(TODAY, find_scenario(name))
        by_month: dict[tuple[int, int], float] = {}
        for d in seed.deliveries:
            key = (d.order_date.year, d.order_date.month)
            by_month[key] = by_month.get(key, 0) + float(d.net_amount)
        totals = [by_month[k] for k in sorted(by_month)][1:-1]
        normal = sum(totals) / len(totals)
        assert all(abs(t - normal) / normal <= 0.05 for t in totals)


class TestTheBaseHistoryIsTheSameEverywhere:
    QUIET = build_story_seed(TODAY, find_scenario("quiet-month"))
    FIRST_CHANGE = {
        "august-contract": date(2026, 7, 13),
        "price-cut": date(2026, 8, 1),
        "supplier-no-effect": date(2026, 12, 31),
        "customer-lost": date(2026, 8, 10),
        "breakdown-shortfall": date(2026, 7, 20),
        "quiet-month": date(2026, 12, 31),
        "two-causes": date(2026, 7, 20),
        "cancellations": date(2026, 8, 1),
        "purchase-price-rise": date(2026, 12, 31),
        "stock-up": date(2026, 12, 31),
        "demand-surge": date(2026, 6, 15),
        "quiet-purchases": date(2026, 12, 31),
        "supplier-switch": date(2026, 12, 31),
        "double-cause": date(2026, 12, 31),
    }

    @pytest.mark.parametrize("name", NAMES)
    def test_orders_before_the_first_order_effect_are_identical(self, name):
        cut = self.FIRST_CHANGE[name]
        seed = build_story_seed(TODAY, find_scenario(name))
        assert [o for o in seed.orders if o.order_date < cut] == [o for o in self.QUIET.orders if o.order_date < cut]
