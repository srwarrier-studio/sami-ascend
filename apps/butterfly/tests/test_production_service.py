import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app, create_app
from butterfly.infrastructure.api.odata import PRODUCTION_ROOT
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.in_memory_production_repo import InMemoryProductionRepo as MemoryProduction
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo as MemoryOrders
from butterfly.infrastructure.memory.production_seed import build_production
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.production_repo import SqliteProductionRepo

TODAY = date(2026, 10, 31)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
PRODUCTION = build_production(STORY, COMPANIES, TODAY)
CONTRACT = (Path(__file__).resolve().parents[3] / "docs/sap/production-contract.md").read_text()
EXAMPLES = re.findall(r"```\nGET \{root\}([^\n]+)\n```\n\n```json\n(.*?)\n```", CONTRACT, re.DOTALL)

MEMORY = TestClient(create_app(MemoryOrders([]), production=MemoryProduction(PRODUCTION.confirmations, PRODUCTION.downtimes)))
SQLITE = TestClient(create_app(MemoryOrders([]), production=SqliteProductionRepo.from_seed(PRODUCTION)))


def get(client: TestClient, path: str):
    response = client.get(PRODUCTION_ROOT.rstrip("/") + "/" + quote(path, safe="/?=&$,()'"))
    return response.status_code, response.json()


def every(entity: str, query: str = "") -> list[dict]:
    found: list[dict] = []
    while True:
        page = get(SQLITE, f"{entity}?$top=1000&$skip={len(found)}{query}")[1]["value"]
        found += page
        if len(page) < 1000:
            return found


CONFIRMATIONS = [
    "ProductionConfirmation?$top=5",
    "ProductionConfirmation?$filter=ProductionOrder eq '0001000417'&$orderby=PostingDate,ConfirmationNumber&$count=true",
    "ProductionConfirmation?$filter=ScrapReason eq 'MACHINE_SETTING' and CompanyCode eq 'INA2'&$orderby=ScrapValue desc&$top=6&$count=true",
    "ProductionConfirmation?$filter=YieldQuantity gt 500.5 and Shift eq 'N'&$top=5&$count=true",
    "ProductionConfirmation?$filter=PostingDate ge 2026-10-01 and PostingDate le 2026-10-31 and WorkCenter eq 'LINE2'&$orderby=PostingDate desc,ConfirmationNumber&$top=8",
    "ProductionConfirmation?$filter=contains(MaterialDescription,'extract') or startswith(Material,'NU')&$count=true&$top=3",
    "ProductionConfirmation?$filter=not (ScrapQuantity eq 0)&$count=true&$top=1",
    "ProductionConfirmation?$select=ConfirmationNumber,YieldValue&$orderby=YieldValue desc&$skip=3&$top=4",
]
DOWNTIMES = [
    "WorkCenterDowntime?$top=5",
    "WorkCenterDowntime?$filter=DowntimeCause eq 'BREAKDOWN'&$count=true",
    "WorkCenterDowntime?$filter=DowntimeHours gt 5.5 and CompanyCode eq 'INA1'&$orderby=DowntimeHours desc&$top=6",
    "WorkCenterDowntime?$filter=PostingDate ge 2026-09-01&$orderby=PostingDate,DowntimeNumber&$count=true&$top=10",
]
SUMMARIES = [
    "ProductionSummaryByDay?$top=10",
    "ProductionSummaryByDay?$filter=CompanyCode eq 'INA1' and PostingDate ge 2026-10-01&$orderby=PostingDate&$count=true",
    "ProductionSummaryByDay?$filter=DowntimeHours gt 5.5&$orderby=DowntimeHours desc&$top=5&$count=true",
    "ProductionSummaryByDay?$filter=GoodValue gt 1000000.5&$orderby=GoodValue desc&$top=4",
    "DowntimeSummaryByDay?$filter=DowntimeCause ne 'CHANGEOVER'&$orderby=PostingDate,DowntimeCause&$top=15&$count=true",
    "DowntimeSummaryByDay?$filter=PostingDate ge 2026-05-01 and PostingDate le 2026-05-31",
    "ScrapSummaryByDay?$filter=ScrapReason eq 'OPERATOR_ERROR'&$orderby=ScrapValue desc&$top=6&$count=true",
    "ScrapSummaryByDay?$filter=CompanyCode eq 'INA3' and PostingDate ge 2026-10-01&$top=20",
    "OutputSummaryByLineShift?$filter=PostingDate eq 2026-10-14",
    "OutputSummaryByLineShift?$filter=Shift eq 'N' and GoodValue gt 100000&$orderby=GoodValue desc&$top=6&$count=true",
]


@pytest.mark.parametrize("path", CONFIRMATIONS + DOWNTIMES + SUMMARIES)
def test_the_database_answers_like_the_lists(path):
    status, body = get(SQLITE, path)
    assert status == 200 and (status, body) == get(MEMORY, path)


@pytest.mark.parametrize("path", ["ProductionConfirmation?$filter=Bogus eq 'x'", "WorkCenterDowntime?$orderby=Nope", "ProductionSummaryByDay?$top=abc", "OutputSummaryByLineShift?$filter=PostingDate eq 'x'"])
def test_a_bad_query_is_refused_the_same_way(path):
    assert get(SQLITE, path) == get(MEMORY, path) and get(SQLITE, path)[0] == 400


class TestRows:
    def test_a_confirmation_has_exactly_the_contract_fields_in_order(self):
        row = get(SQLITE, "ProductionConfirmation?$top=1")[1]["value"][0]
        assert list(row) == [
            "ConfirmationNumber", "ConfirmationCounter", "ProductionOrder", "Material", "MaterialDescription", "Plant", "WorkCenter", "WorkCenterName", "Shift", "PostingDate",
            "YieldQuantity", "ScrapQuantity", "TargetQuantity", "QuantityUnit", "ScrapReason", "RunHours", "YieldValue", "ScrapValue", "TargetValue", "Currency", "CompanyCode",
        ]
        assert row["WorkCenterName"].startswith("Line ") and row["RunHours"] == "8.00"

    def test_a_downtime_has_exactly_the_contract_fields_in_order(self):
        row = get(SQLITE, "WorkCenterDowntime?$top=1")[1]["value"][0]
        assert list(row) == ["DowntimeNumber", "ProductionOrder", "Plant", "WorkCenter", "WorkCenterName", "PostingDate", "DowntimeHours", "DowntimeCause", "CompanyCode"]

    def test_one_row_by_key_and_expand_are_refused_and_an_unknown_entity_is_404(self):
        assert SQLITE.get(PRODUCTION_ROOT + "ProductionConfirmation('1')").status_code == 404
        assert SQLITE.get(PRODUCTION_ROOT + "ProductionConfirmation?$expand=_Item").status_code == 400
        assert SQLITE.get(PRODUCTION_ROOT + "Nope").status_code == 404


class TestSummaryTotals:
    def test_a_day_is_the_sum_of_its_confirmations_and_stoppages(self):
        day = every("ProductionSummaryByDay", "&$filter=PostingDate eq 2026-10-14 and CompanyCode eq 'INA1'")[0]
        confirmations = every("ProductionConfirmation", "&$filter=PostingDate eq 2026-10-14 and CompanyCode eq 'INA1'")
        stops = every("WorkCenterDowntime", "&$filter=PostingDate eq 2026-10-14 and CompanyCode eq 'INA1'")
        assert Decimal(day["GoodValue"]) == sum((Decimal(c["YieldValue"]) for c in confirmations), Decimal(0))
        assert Decimal(day["ScrapValue"]) == sum((Decimal(c["ScrapValue"]) for c in confirmations), Decimal(0))
        assert Decimal(day["TargetValue"]) == sum((Decimal(c["TargetValue"]) for c in confirmations), Decimal(0))
        assert Decimal(day["PlannedHours"]) == Decimal("8.00") * len(confirmations) and day["ConfirmationCount"] == len(confirmations)
        assert Decimal(day["DowntimeHours"]) == sum((Decimal(s["DowntimeHours"]) for s in stops), Decimal(0))

    def test_the_daily_downtime_hours_add_up_to_every_stoppage(self):
        assert sum(Decimal(r["DowntimeHours"]) for r in every("ProductionSummaryByDay")) == sum(Decimal(r["DowntimeHours"]) for r in every("WorkCenterDowntime"))

    def test_downtime_by_cause_adds_up_to_the_events(self):
        rows = every("DowntimeSummaryByDay")
        assert sum(r["EventCount"] for r in rows) == len(every("WorkCenterDowntime"))
        assert sum(Decimal(r["DowntimeHours"]) for r in rows) == sum(Decimal(r["DowntimeHours"]) for r in every("WorkCenterDowntime"))

    def test_scrap_by_reason_leaves_out_confirmations_without_scrap(self):
        rows = every("ScrapSummaryByDay")
        scrapped = [c for c in every("ProductionConfirmation") if c["ScrapReason"] is not None]
        assert sum(r["ConfirmationCount"] for r in rows) == len(scrapped)
        assert sum(Decimal(r["ScrapValue"]) for r in rows) == sum(Decimal(c["ScrapValue"]) for c in scrapped)

    def test_lines_and_shifts_add_up_to_the_good_value_of_the_day(self):
        by_day: dict[tuple, Decimal] = {}
        for r in every("OutputSummaryByLineShift"):
            key = (r["PostingDate"], r["CompanyCode"])
            by_day[key] = by_day.get(key, Decimal(0)) + Decimal(r["GoodValue"])
        assert by_day == {(r["PostingDate"], r["CompanyCode"]): Decimal(r["GoodValue"]) for r in every("ProductionSummaryByDay")}

    def test_effectiveness_can_be_worked_out_from_the_daily_summary(self):
        rows = every("ProductionSummaryByDay", "&$filter=PostingDate ge 2026-09-01 and PostingDate le 2026-10-31")
        planned, down = sum(Decimal(r["PlannedHours"]) for r in rows), sum(Decimal(r["DowntimeHours"]) for r in rows)
        good, scrap, target = (sum(Decimal(r[k]) for r in rows) for k in ("GoodValue", "ScrapValue", "TargetValue"))
        availability, performance, quality = 1 - down / planned, (good + scrap) / target, good / (good + scrap)
        assert Decimal("0.7") < availability < 1 and Decimal("0.9") < performance < Decimal("1.1") and Decimal("0.95") < quality < 1


class TestContractExamples:
    def test_the_contract_has_an_example_for_every_entity(self):
        assert len(EXAMPLES) == 6

    @pytest.mark.parametrize("request_text,response_text", EXAMPLES, ids=[e[0][:50] for e in EXAMPLES])
    def test_the_data_gives_exactly_the_example(self, request_text, response_text):
        for client in (MEMORY, SQLITE):
            response = client.get(PRODUCTION_ROOT + request_text)
            assert response.status_code == 200
            assert response.json() == json.loads(response_text)


class TestRunner:
    def test_the_story_seed_serves_the_shop_floor_and_the_small_seed_none(self, tmp_path):
        story = TestClient(build_default_app(TODAY, "story", "august-contract", str(tmp_path / "a.db")))
        small = TestClient(build_default_app(TODAY, "small", "august-contract", str(tmp_path / "b.db")))
        assert story.get(PRODUCTION_ROOT + "ProductionConfirmation?$count=true&$top=1").json()["@odata.count"] == len(PRODUCTION.confirmations)
        assert small.get(PRODUCTION_ROOT + "ProductionConfirmation?$count=true&$top=1").json()["@odata.count"] == 0
