import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app, create_app
from butterfly.infrastructure.api.odata import INVENTORY_ROOT, ROOT
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.in_memory_inventory_repo import InMemoryInventoryRepo as MemoryInventory
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo as MemoryOrders
from butterfly.infrastructure.memory.inventory_seed import build_inventory
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.inventory_repo import SqliteInventoryRepo

TODAY = date(2026, 10, 31)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
INVENTORY = build_inventory(STORY, COMPANIES, TODAY)
CONTRACT = (Path(__file__).resolve().parents[3] / "docs/sap/inventory-contract.md").read_text()
EXAMPLES = re.findall(r"```\nGET \{root\}([^\n]+)\n```\n\n```json\n(.*?)\n```", CONTRACT, re.DOTALL)


def memory_client() -> TestClient:
    return TestClient(create_app(MemoryOrders([]), inventory=MemoryInventory(INVENTORY.stocks, INVENTORY.movements, INVENTORY.monthly)))


def sqlite_client() -> TestClient:
    return TestClient(create_app(MemoryOrders([]), inventory=SqliteInventoryRepo.from_seed(INVENTORY)))


MEMORY, SQLITE = memory_client(), sqlite_client()


def get(client: TestClient, path: str):
    response = client.get(INVENTORY_ROOT.rstrip("/") + "/" + quote(path, safe="/?=&$,()'"))
    return response.status_code, response.json()


STOCK = [
    "MaterialStock?$top=5",
    "MaterialStock?$filter=StockStatus ne 'O'&$orderby=Material,Plant,StorageLocation",
    "MaterialStock?$filter=StockStatus eq 'Z' and CompanyCode eq 'INA2'&$count=true",
    "MaterialStock?$filter=StockValue gt 1000000.5&$orderby=StockValue desc&$top=6",
    "MaterialStock?$filter=MaterialGroup eq 'BOTANIC' or MaterialGroup eq 'ESSOIL'&$orderby=MaterialGroup,Material&$count=true",
    "MaterialStock?$filter=contains(MaterialDescription,'oil') and LastMovementDate ge 2026-10-01&$count=true",
    "MaterialStock?$filter=ReorderLevel gt 100.5 and Plant eq '1000'&$select=Material,StockQuantity,ReorderLevel&$orderby=StockQuantity desc",
    "MaterialStock?$filter=not (StockStatus eq 'O')&$count=true",
    "MaterialStock?$skip=30&$top=10&$count=true",
]
MOVEMENTS = [
    "StockMovement?$top=5",
    "StockMovement?$filter=Material eq 'RAW-2002' and PostingDate ge 2026-10-01 and PostingDate le 2026-10-31&$orderby=PostingDate,MaterialDocument,MaterialDocumentItem,MaterialDocumentYear",
    "StockMovement?$filter=MovementType eq '702'&$count=true",
    "StockMovement?$filter=DebitCreditCode eq 'H' and Amount gt 100000&$orderby=Amount desc&$top=8&$count=true",
    "StockMovement?$filter=EntryDateTime ge 2026-10-30T00:00:00Z&$orderby=EntryDateTime desc&$top=6",
    "StockMovement?$filter=Quantity gt 5000.5 and CompanyCode eq 'INA1'&$top=4&$count=true",
    "StockMovement?$filter=startswith(Material,'RAW') and PostingDate eq 2026-09-15",
    "StockMovement?$select=MaterialDocument,Amount&$orderby=MaterialDocument desc&$top=3",
]


@pytest.mark.parametrize("path", STOCK + MOVEMENTS)
def test_the_database_answers_like_the_lists(path):
    status, body = get(SQLITE, path)
    assert status == 200 and (status, body) == get(MEMORY, path)


@pytest.mark.parametrize("path", ["MaterialStock?$filter=Bogus eq 'x'", "MaterialStock?$filter=StockQuantity lt ReorderLevel", "StockMovement?$orderby=Nope", "MaterialStock?$top=abc", "StockMovement?$filter=PostingDate eq 'x'"])
def test_a_bad_query_is_refused_the_same_way(path):
    assert get(SQLITE, path) == get(MEMORY, path) and get(SQLITE, path)[0] == 400


class TestRows:
    def first(self, client, path):
        return get(client, path)[1]["value"][0]

    def test_a_stock_row_has_exactly_the_contract_fields_in_order(self):
        row = self.first(SQLITE, "MaterialStock?$top=1")
        assert list(row) == ["Material", "MaterialDescription", "MaterialGroup", "MaterialGroupName", "Plant", "StorageLocation", "StorageLocationName", "StockQuantity", "QuantityUnit", "StockValue", "Currency", "ReorderLevel", "StockStatus", "LastMovementDate", "CompanyCode"]
        assert row["StockStatus"] in "OLZ" and row["Currency"] == "INR" and row["MaterialGroupName"] and row["StorageLocationName"]

    def test_a_movement_row_has_exactly_the_contract_fields_in_order(self):
        row = self.first(SQLITE, "StockMovement?$top=1")
        assert list(row) == ["MaterialDocument", "MaterialDocumentItem", "MaterialDocumentYear", "PostingDate", "EntryDateTime", "Material", "MaterialDescription", "Plant", "StorageLocation", "MovementType", "DebitCreditCode", "Quantity", "QuantityUnit", "Amount", "Currency", "CompanyCode"]
        assert row["EntryDateTime"].endswith("Z") and len(row["MaterialDocument"]) == 10

    def test_status_zero_low_and_ok_follow_the_quantities(self):
        for row in get(SQLITE, "MaterialStock?$top=100")[1]["value"]:
            quantity, level = float(row["StockQuantity"]), float(row["ReorderLevel"])
            assert row["StockStatus"] == ("Z" if quantity == 0 else "L" if quantity < level else "O")

    def test_the_status_filter_returns_what_comparing_in_code_returns(self):
        rows = get(SQLITE, "MaterialStock?$top=100")[1]["value"]
        low = {r["Material"] for r in rows if float(r["StockQuantity"]) < float(r["ReorderLevel"]) or float(r["StockQuantity"]) == 0}
        assert {r["Material"] for r in get(SQLITE, "MaterialStock?$filter=StockStatus ne 'O'")[1]["value"]} == low

    def test_one_row_by_key_and_expand_are_refused(self):
        assert SQLITE.get(INVENTORY_ROOT + "MaterialStock('RAW-2002')").status_code == 404
        assert SQLITE.get(INVENTORY_ROOT + "MaterialStock?$expand=_Item").status_code == 400

    def test_an_unknown_entity_is_404(self):
        assert SQLITE.get(INVENTORY_ROOT + "Nope").status_code == 404


class TestContractExamples:
    def test_the_contract_has_examples(self):
        assert len(EXAMPLES) >= 2

    @pytest.mark.parametrize("request_text,response_text", EXAMPLES, ids=[e[0][:50] for e in EXAMPLES])
    def test_the_data_gives_exactly_the_example(self, request_text, response_text):
        for client in (MEMORY, SQLITE):
            response = client.get(INVENTORY_ROOT + request_text)
            assert response.status_code == 200
            assert response.json() == json.loads(response_text)


class TestRunner:
    def test_the_story_seed_serves_stock_and_the_small_seed_serves_none(self, tmp_path):
        story = TestClient(build_default_app(TODAY, "story", "august-contract", str(tmp_path / "a.db")))
        small = TestClient(build_default_app(TODAY, "small", "august-contract", str(tmp_path / "b.db")))
        assert story.get(INVENTORY_ROOT + "MaterialStock?$count=true&$top=1").json()["@odata.count"] == 36
        assert small.get(INVENTORY_ROOT + "MaterialStock?$count=true&$top=1").json()["@odata.count"] == 0
        assert story.get(ROOT + "SalesOrder?$top=1").status_code == 200
