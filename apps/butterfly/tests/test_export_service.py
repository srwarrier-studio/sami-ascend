import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app, create_app
from butterfly.infrastructure.api.odata import EXPORT_ROOT
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.export_seed import build_exports
from butterfly.infrastructure.memory.in_memory_export_repo import InMemoryExportRepo as MemoryExports
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo as MemoryOrders
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.export_repo import SqliteExportRepo

TODAY = date(2026, 10, 31)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
SHIPMENTS = build_exports(STORY, TODAY)
CONTRACT = (Path(__file__).resolve().parents[3] / "docs/sap/export-contract.md").read_text()
EXAMPLES = re.findall(r"```\nGET \{root\}([^\n]+)\n```\n\n```json\n(.*?)\n```", CONTRACT, re.DOTALL)

MEMORY = TestClient(create_app(MemoryOrders([]), exports=MemoryExports(SHIPMENTS)))
SQLITE = TestClient(create_app(MemoryOrders([]), exports=SqliteExportRepo.from_shipments(SHIPMENTS)))


def get(client: TestClient, path: str):
    response = client.get(EXPORT_ROOT.rstrip("/") + "/" + quote(path, safe="/?=&$,()'"))
    return response.status_code, response.json()


def every(entity: str, query: str = "") -> list[dict]:
    found: list[dict] = []
    while True:
        page = get(SQLITE, f"{entity}?$top=1000&$skip={len(found)}{query}")[1]["value"]
        found += page
        if len(page) < 1000:
            return found


QUERIES = [
    "ExportShipment?$top=5",
    "ExportShipment?$filter=ShipmentStatus eq 'T'&$orderby=ExpectedArrivalDate,Shipment&$count=true&$top=10",
    "ExportShipment?$filter=Country eq 'US' and TransportMode eq 'A' and ShipmentDate ge 2026-10-01&$orderby=NetAmount desc&$top=6&$count=true",
    "ExportShipment?$filter=NetAmount gt 5000000.5 and CompanyCode eq 'INA1'&$orderby=NetAmount desc,Shipment&$top=5",
    "ExportShipment?$filter=ActualArrivalDate gt 2026-10-20 and DocumentCurrency eq 'USD'&$count=true&$top=3",
    "ExportShipment?$filter=contains(CustomerName,'Trading') or startswith(CountryName,'Un')&$count=true&$top=4",
    "ExportShipment?$filter=not (ShipmentStatus eq 'D')&$count=true&$top=1",
    "ExportShipment?$select=Shipment,NetAmount&$orderby=Shipment desc&$skip=10&$top=4",
    "ExportSummaryByDay?$top=10",
    "ExportSummaryByDay?$filter=ShipmentDate ge 2026-10-01 and CompanyCode eq 'INA2'&$orderby=ShipmentDate&$count=true&$top=40",
    "ExportSummaryByDay?$filter=NetAmount gt 10000000.5&$orderby=NetAmount desc&$top=5&$count=true",
    "ExportSummaryByDestination?$filter=ShipmentDate ge 2026-10-01&$orderby=NetAmount desc&$top=8&$count=true",
    "ExportSummaryByDestination?$filter=Country eq 'JP' and CompanyCode eq 'INA3'&$top=10",
    "ExportSummaryByMode?$filter=TransportMode ne 'S' and ShipmentDate ge 2026-10-15&$orderby=ShipmentDate,TransportMode&$count=true&$top=30",
    "ExportSummaryByMode?$filter=ShipmentCount ge 2&$top=5&$count=true",
]


@pytest.mark.parametrize("path", QUERIES)
def test_the_database_answers_like_the_lists(path):
    status, body = get(SQLITE, path)
    assert status == 200 and (status, body) == get(MEMORY, path)


@pytest.mark.parametrize("path", ["ExportShipment?$filter=Bogus eq 'x'", "ExportSummaryByDay?$orderby=Nope", "ExportShipment?$top=abc", "ExportSummaryByMode?$filter=ShipmentDate eq 'x'"])
def test_a_bad_query_is_refused_the_same_way(path):
    assert get(SQLITE, path) == get(MEMORY, path) and get(SQLITE, path)[0] == 400


class TestRows:
    def test_a_shipment_has_exactly_the_contract_fields_in_order(self):
        row = get(SQLITE, "ExportShipment?$top=1")[1]["value"][0]
        assert list(row) == [
            "Shipment", "SalesOrder", "SoldToParty", "CustomerName", "Country", "CountryName", "TransportMode", "ShipmentDate", "ExpectedArrivalDate", "ActualArrivalDate",
            "ShipmentStatus", "NetAmount", "Currency", "DocumentAmount", "DocumentCurrency", "CompanyCode",
        ]
        assert row["Currency"] == "INR" and row["Shipment"].startswith("60")

    def test_one_row_by_key_and_expand_are_refused_and_an_unknown_entity_is_404(self):
        assert SQLITE.get(EXPORT_ROOT + "ExportShipment('1')").status_code == 404
        assert SQLITE.get(EXPORT_ROOT + "ExportShipment?$expand=_Item").status_code == 400
        assert SQLITE.get(EXPORT_ROOT + "Nope").status_code == 404


class TestSummaryTotals:
    def test_a_day_equals_the_shipments_of_that_day(self):
        day = every("ExportSummaryByDay", "&$filter=ShipmentDate eq 2026-10-14 and CompanyCode eq 'INA1'")[0]
        mine = [s for s in SHIPMENTS if str(s.shipment_date) == "2026-10-14" and s.company_code == "INA1"]
        assert day["ShipmentCount"] == len(mine) and Decimal(day["NetAmount"]) == sum((s.net_amount for s in mine), Decimal(0))

    def test_destinations_and_modes_add_up_to_the_days(self):
        days = {(r["ShipmentDate"], r["CompanyCode"]): (r["ShipmentCount"], Decimal(r["NetAmount"])) for r in every("ExportSummaryByDay")}
        by_destination: dict[tuple, list] = {}
        for r in every("ExportSummaryByDestination"):
            entry = by_destination.setdefault((r["ShipmentDate"], r["CompanyCode"]), [0, Decimal(0)])
            entry[0] += r["ShipmentCount"]
            entry[1] += Decimal(r["NetAmount"])
        by_mode: dict[tuple, int] = {}
        for r in every("ExportSummaryByMode"):
            key = (r["ShipmentDate"], r["CompanyCode"])
            by_mode[key] = by_mode.get(key, 0) + r["ShipmentCount"]
        assert by_destination == {k: [v[0], v[1]] for k, v in days.items()}
        assert by_mode == {k: v[0] for k, v in days.items()}

    def test_the_summaries_cover_every_shipment(self):
        assert sum(r["ShipmentCount"] for r in every("ExportSummaryByDay")) == len(SHIPMENTS) == len(every("ExportShipment"))

    def test_in_transit_by_filter_equals_in_transit_by_dates(self):
        found = every("ExportShipment", "&$filter=ShipmentStatus eq 'T'")
        assert len(found) == sum(1 for s in SHIPMENTS if s.actual_arrival_date is None) and all(r["ActualArrivalDate"] is None for r in found)


class TestContractExamples:
    def test_the_contract_has_an_example_for_every_entity(self):
        assert len(EXAMPLES) == 4

    @pytest.mark.parametrize("request_text,response_text", EXAMPLES, ids=[e[0][:50] for e in EXAMPLES])
    def test_the_data_gives_exactly_the_example(self, request_text, response_text):
        for client in (MEMORY, SQLITE):
            response = client.get(EXPORT_ROOT + request_text)
            assert response.status_code == 200
            assert response.json() == json.loads(response_text)


class TestRunner:
    def test_the_story_seed_serves_shipments_and_the_small_seed_none(self, tmp_path):
        story = TestClient(build_default_app(TODAY, "story", "august-contract", str(tmp_path / "a.db")))
        small = TestClient(build_default_app(TODAY, "small", "august-contract", str(tmp_path / "b.db")))
        assert story.get(EXPORT_ROOT + "ExportShipment?$count=true&$top=1").json()["@odata.count"] == len(SHIPMENTS)
        assert small.get(EXPORT_ROOT + "ExportShipment?$count=true&$top=1").json()["@odata.count"] == 0
