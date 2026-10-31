import json
import re
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app, create_app
from butterfly.infrastructure.api.odata import DRIVERS_ROOT, ROOT
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from butterfly.infrastructure.memory.story_seed import build_story_seed

TODAY = date(2026, 10, 31)
CONTRACT = (Path(__file__).resolve().parents[3] / "docs/sap/drivers-contract.md").read_text()
EXAMPLE = re.compile(r"```\nGET \{root\}([^\n]+)\n```\n\n```json\n(.*?)\n```", re.DOTALL)
EXAMPLES = EXAMPLE.findall(CONTRACT)


def story_client() -> TestClient:
    story = build_story_seed(TODAY)
    drivers = InMemoryDriverRepo(story.contracts, story.deliveries, story.production_orders, story.components)
    return TestClient(create_app(InMemorySalesOrderRepo(story.orders), drivers=drivers))


class TestContractExamples:
    def test_every_entity_has_an_example(self):
        assert len(EXAMPLES) == 5

    @pytest.mark.parametrize("request_text,response_text", EXAMPLES, ids=[e[0][:50] for e in EXAMPLES])
    def test_the_story_data_gives_exactly_the_example(self, request_text, response_text):
        response = story_client().get(DRIVERS_ROOT + request_text)
        assert response.status_code == 200
        assert response.json() == json.loads(response_text)


class TestRunnerSeed:
    def test_the_story_seed_serves_history_and_drivers(self):
        client = TestClient(build_default_app(TODAY, "story"))
        assert client.get(ROOT + "SalesOrder?$top=1&$count=true").json()["@odata.count"] > 1000
        assert client.get(DRIVERS_ROOT + "SalesContract?$count=true").json()["@odata.count"] >= 10

    def test_the_small_seed_is_the_old_thirty_orders_and_no_drivers(self):
        client = TestClient(build_default_app(TODAY, "small"))
        assert client.get(ROOT + "SalesOrder?$top=1&$count=true").json()["@odata.count"] == 30
        assert client.get(DRIVERS_ROOT + "SalesContract?$count=true").json()["@odata.count"] == 0

    def test_the_story_seed_is_the_default(self, monkeypatch):
        monkeypatch.delenv("BUTTERFLY_SEED", raising=False)
        assert TestClient(build_default_app(TODAY)).get(DRIVERS_ROOT + "SalesContract?$count=true").json()["@odata.count"] > 0

    def test_the_environment_chooses_the_seed(self, monkeypatch):
        monkeypatch.setenv("BUTTERFLY_SEED", "small")
        assert TestClient(build_default_app(TODAY)).get(ROOT + "SalesOrder?$top=1&$count=true").json()["@odata.count"] == 30

    def test_an_unknown_seed_stops_the_start_with_a_clear_message(self):
        with pytest.raises(SystemExit, match="BUTTERFLY_SEED must be 'story' or 'small'"):
            build_default_app(TODAY, "nonsense")

    def test_a_new_order_continues_after_the_last_story_order(self):
        client = TestClient(build_default_app(TODAY, "story"))
        last = client.get(ROOT + "SalesOrder?$orderby=SalesOrder desc&$top=1&$select=SalesOrder").json()["value"][0]["SalesOrder"]
        created = client.post(ROOT + "SalesOrder", json={"SalesOrderType": "OR", "SoldToParty": "0000100002", "TransactionCurrency": "INR", "_Item": [{"Material": "RM-1003", "Quantity": "12.5", "QuantityUnit": "KG"}]})
        assert created.status_code == 201
        assert int(created.json()["SalesOrder"]) == int(last) + 1

    def test_the_sales_summaries_show_the_story(self):
        client = TestClient(build_default_app(TODAY, "story"))
        july = client.get(ROOT + "SalesSummaryByDay?$filter=OrderDate ge 2026-07-01 and OrderDate le 2026-07-31&$count=true").json()
        assert july["@odata.count"] == 23
