from datetime import date
from decimal import Decimal
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.api.odata import DRIVERS_ROOT
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo as MemoryDrivers
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo as MemoryOrders
from butterfly.infrastructure.memory.inventory_master import GROUP_OF
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.driver_repo import SqliteDriverRepo

TODAY = date(2026, 10, 31)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
ARGS = (STORY.contracts, STORY.deliveries, STORY.production_orders, STORY.components, STORY.invoices)
MEMORY = TestClient(create_app(MemoryOrders([]), drivers=MemoryDrivers(*ARGS)))
SQLITE = TestClient(create_app(MemoryOrders([]), drivers=SqliteDriverRepo.from_lists(*ARGS)))


def get(client: TestClient, path: str):
    response = client.get(DRIVERS_ROOT.rstrip("/") + "/" + quote(path, safe="/?=&$,()'"))
    return response.status_code, response.json()


def every(entity: str, query: str = "") -> list[dict]:
    found: list[dict] = []
    while True:
        page = get(SQLITE, f"{entity}?$top=1000&$skip={len(found)}{query}")[1]["value"]
        found += page
        if len(page) < 1000:
            return found


QUERIES = [
    "PurchaseSummaryByMaterialGroup?$top=10&$count=true",
    "PurchaseSummaryByMaterialGroup?$filter=MaterialGroup eq 'BOTANIC' and OrderDate ge 2026-06-01&$orderby=OrderDate,MaterialGroup&$top=20&$count=true",
    "PurchaseSummaryByMaterialGroup?$filter=CompanyCode eq 'INA2' and TotalNetAmount gt 1000000.5&$orderby=TotalNetAmount desc&$top=8",
    "PurchaseSummaryByMaterialGroup?$filter=contains(MaterialGroupName,'raw') or MaterialGroup eq 'PACKING'&$orderby=OrderDate desc,MaterialGroup&$top=12",
    "PurchaseSummaryByMaterialGroup?$filter=OrderCount ge 2 and Currency eq 'USD'&$count=true&$top=3",
    "PurchaseSummaryByMaterialGroup?$select=MaterialGroup,TotalNetAmount&$orderby=TotalNetAmount&$skip=5&$top=5",
]


@pytest.mark.parametrize("path", QUERIES)
def test_the_view_answers_like_the_lists(path):
    status, body = get(SQLITE, path)
    assert status == 200 and (status, body) == get(MEMORY, path)


def test_the_groups_add_up_to_the_day_summary():
    by_group: dict[tuple, Decimal] = {}
    for row in every("PurchaseSummaryByMaterialGroup"):
        key = (row["OrderDate"], row["Currency"], row["CompanyCode"])
        by_group[key] = by_group.get(key, Decimal(0)) + Decimal(row["TotalNetAmount"])
    by_day = {(r["OrderDate"], r["Currency"], r["CompanyCode"]): Decimal(r["TotalNetAmount"]) for r in every("PurchaseSummaryByDay")}
    assert by_group == by_day


def test_a_row_equals_a_hand_total_of_its_deliveries():
    row = next(r for r in every("PurchaseSummaryByMaterialGroup", "&$filter=MaterialGroup eq 'BOTANIC' and CompanyCode eq 'INA1'") if r["OrderCount"] >= 1)
    mine = [d for d in STORY.deliveries if d.delivery_status != "X" and GROUP_OF[d.material] == "BOTANIC" and d.company_code == "INA1" and str(d.order_date) == row["OrderDate"] and d.transaction_currency == row["Currency"]]
    assert Decimal(row["TotalNetAmount"]) == sum((d.net_amount for d in mine), Decimal(0)) and row["OrderCount"] == len(mine)


def test_cancelled_items_are_left_out():
    cancelled = [d for d in STORY.deliveries if d.delivery_status == "X"]
    counted = sum(r["OrderCount"] for r in every("PurchaseSummaryByMaterialGroup"))
    assert counted == len([d for d in STORY.deliveries if d.delivery_status != "X"]) and len(cancelled) >= 0


def test_a_row_names_its_group():
    assert {r["MaterialGroup"]: r["MaterialGroupName"] for r in every("PurchaseSummaryByMaterialGroup")}["BOTANIC"] == "Botanical raw materials"
