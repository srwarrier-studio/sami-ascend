from datetime import date
from decimal import Decimal

import httpx
import pytest
from urllib.parse import unquote

from synapse_api.application.catalog import GetWidgetData, ListCatalog
from synapse_api.application.production_widgets import production_catalog
from synapse_api.domain.entities.production import DowntimeDay, LineShiftOutput, OpenOrder, ProductionDay, ScrapDay
from synapse_api.infrastructure.butterfly_production_source import ButterflyProductionSource
from synapse_api.infrastructure.mock_production_source import MockProductionSource
from synapse_api.infrastructure.odata_reader import ODataReader

TODAY = date(2026, 11, 3)


def data(source: MockProductionSource, entry_id: str, currency: str = "INR", top: int = 5) -> dict:
    return GetWidgetData(production_catalog(source)).execute(entry_id, TODAY, currency, top)


def day(d: date, good="100", scrap="10", target="120", planned="8", down="1", currency="INR") -> ProductionDay:
    return ProductionDay(d, Decimal(planned), Decimal(down), Decimal(target), Decimal(good), Decimal(scrap), currency)


class TestList:
    def test_lists_the_seven_production_widgets_under_their_old_ids(self):
        entries = ListCatalog(production_catalog(MockProductionSource())).execute()
        assert [e.id for e in entries] == ["prod-output", "prod-oee", "prod-plan", "prod-downtime", "prod-scrap", "prod-heat", "prod-orders"]
        assert {e.category for e in entries} == {"Production"}


class TestOutput:
    def source(self):
        return MockProductionSource(days=[day(date(2026, 10, 20), "300"), day(date(2026, 10, 5), "100"), day(date(2026, 9, 20), "200"), day(date(2026, 6, 1), "50"), day(date(2026, 10, 20), "999", currency="USD")])

    def test_is_the_last_30_days_against_the_30_before_with_six_windows_as_the_trend(self):
        props = data(self.source(), "prod-output")
        assert props["value"] == 400.0 and props["delta"] == pytest.approx(1.0)
        assert len(props["trend"]) == 6 and props["trend"][-1] == 400.0 and props["trend"][-2] == 200.0 and props["trend"][0] == 50.0
        assert props["title"] == "Output, last 30 days" and props["caption"] == "last 30 days vs the 30 before"

    def test_without_the_window_before_there_is_no_delta(self):
        assert "delta" not in data(MockProductionSource(days=[day(date(2026, 10, 20), "300")]), "prod-output")


class TestEffectiveness:
    def test_is_availability_times_performance_times_quality(self):
        source = MockProductionSource(days=[day(date(2026, 10, 20), good="90", scrap="10", target="125", planned="10", down="2"), day(date(2026, 10, 21), good="90", scrap="10", target="125", planned="10", down="2")])
        props = data(source, "prod-oee")
        assert props["value"] == pytest.approx(0.8 * (200 / 250) * (180 / 200)) and props["target"] == 0.85 and props["caption"] == "last 30 days"

    def test_no_production_is_zero_with_a_caption(self):
        props = data(MockProductionSource(days=[day(date(2026, 8, 1))]), "prod-oee")
        assert (props["value"], props["caption"]) == (0.0, "no production in 30 days")


class TestPlan:
    def test_has_six_months_of_output_against_plan(self):
        source = MockProductionSource(days=[day(date(2026, 10, 5), "100", target="120"), day(date(2026, 10, 6), "50", target="60"), day(date(2026, 7, 5), "70", target="80"), day(date(2026, 3, 1), "9", target="9")])
        props = data(source, "prod-plan")
        assert [p["label"] for p in props["data"]] == ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
        assert [p["value"] for p in props["data"]] == [0.0, 70.0, 0.0, 0.0, 150.0, 0.0]
        assert [p["value"] for p in props["compare"]] == [0.0, 80.0, 0.0, 0.0, 180.0, 0.0]
        assert (props["label"], props["compareLabel"]) == ("Output", "Plan")


class TestLosses:
    def test_downtime_is_by_cause_biggest_first_over_90_days(self):
        source = MockProductionSource(downtimes=[DowntimeDay(date(2026, 10, 1), "CHANGEOVER", Decimal("30")), DowntimeDay(date(2026, 10, 2), "BREAKDOWN", Decimal("48")), DowntimeDay(date(2026, 10, 3), "CHANGEOVER", Decimal("20")), DowntimeDay(date(2026, 1, 1), "OTHER", Decimal("999"))])
        assert data(source, "prod-downtime")["data"] == [{"label": "Changeover", "value": 50.0}, {"label": "Breakdown", "value": 48.0}]

    def test_scrap_is_by_reason_biggest_first_and_leaves_out_other_currencies(self):
        source = MockProductionSource(scraps=[ScrapDay(date(2026, 10, 1), "MACHINE_SETTING", Decimal("70"), "INR"), ScrapDay(date(2026, 10, 2), "OPERATOR_ERROR", Decimal("100"), "INR"), ScrapDay(date(2026, 10, 3), "OTHER", Decimal("5"), "USD")])
        assert data(source, "prod-scrap")["slices"] == [{"label": "Operator error", "value": 100.0}, {"label": "Machine setting", "value": 70.0}]


class TestHeat:
    def test_adds_plants_together_per_line_and_shift_in_words(self):
        source = MockProductionSource(
            lines=[LineShiftOutput(date(2026, 10, 20), "LINE1", "Line 1", "M", Decimal("10"), "INR"), LineShiftOutput(date(2026, 10, 21), "LINE1", "Line 1", "M", Decimal("5"), "INR"), LineShiftOutput(date(2026, 10, 21), "LINE2", "Line 2", "N", Decimal("7"), "INR"), LineShiftOutput(date(2026, 8, 1), "LINE1", "Line 1", "A", Decimal("99"), "INR")]
        )
        assert data(source, "prod-heat")["cells"] == [{"row": "Line 1", "column": "Morning", "value": 15.0}, {"row": "Line 2", "column": "Night", "value": 7.0}]


class TestOrders:
    def test_lists_open_orders_earliest_first_with_a_status_word(self):
        source = MockProductionSource(
            orders=[
                OpenOrder("3", "Later", Decimal("10"), date(2026, 11, 20), date(2026, 12, 4)),
                OpenOrder("1", "Late one", Decimal("20"), date(2026, 10, 1), date(2026, 10, 15)),
                OpenOrder("2", "Running", Decimal("30"), date(2026, 10, 28), date(2026, 11, 10)),
            ]
        )
        rows = data(source, "prod-orders")["rows"]
        assert [(r["order"], r["status"]) for r in rows] == [("1", "Late"), ("2", "In progress"), ("3", "Planned")]
        assert rows[0]["quantity"] == 20.0 and rows[0]["item"] == "Late one"


class TestButterflySource:
    def source(self, rows, urls):
        def handler(request):
            urls.append(unquote(str(request.url)))
            return httpx.Response(200, json={"value": rows})

        reader = ODataReader("http://sap/production/", 5, httpx.MockTransport(handler))
        orders = ODataReader("http://sap/drivers/", 5, httpx.MockTransport(handler))
        return ButterflyProductionSource(reader, orders)

    def test_day_summaries_ask_for_the_range_and_company(self):
        urls = []
        row = {"PostingDate": "2026-10-14", "PlannedHours": "16.00", "DowntimeHours": "2.00", "TargetValue": "100.00", "GoodValue": "90.00", "ScrapValue": "5.00", "ConfirmationCount": 2, "Currency": "INR"}
        result = self.source([row], urls).for_companies(("INA1",)).day_summaries(date(2026, 10, 1), date(2026, 10, 31))
        assert (result[0].good, result[0].downtime_hours) == (Decimal("90.00"), Decimal("2.00"))
        assert "ProductionSummaryByDay?$filter=PostingDate ge 2026-10-01 and PostingDate le 2026-10-31 and (CompanyCode eq 'INA1')&$orderby=PostingDate,Currency,CompanyCode" in urls[0]

    def test_the_other_summaries_read_their_entities(self):
        urls = []
        start, end = date(2026, 10, 1), date(2026, 10, 31)
        down = {"PostingDate": "2026-10-10", "DowntimeCause": "BREAKDOWN", "DowntimeHours": "48.00", "EventCount": 1}
        scrap = {"PostingDate": "2026-10-10", "ScrapReason": "OTHER", "ScrapValue": "3.00", "Currency": "INR", "ConfirmationCount": 1}
        line = {"PostingDate": "2026-10-10", "WorkCenter": "LINE1", "Shift": "M", "WorkCenterName": None, "GoodValue": "9.00", "Currency": "INR"}
        assert self.source([down], urls).downtime_summaries(start, end)[0].cause == "BREAKDOWN"
        assert self.source([scrap], urls).scrap_summaries(start, end)[0].value == Decimal("3.00")
        assert self.source([line], urls).line_shift_output(start, end)[0].name == "LINE1"
        assert "DowntimeSummaryByDay?" in urls[0] and "ScrapSummaryByDay?" in urls[1] and "OutputSummaryByLineShift?" in urls[2]

    def test_open_orders_come_from_the_drivers_service_by_status_and_start(self):
        urls = []
        row = {"ProductionOrder": "0001000440", "Material": "RM-1001", "MaterialDescription": None, "PlannedQuantity": "3500.000", "PlannedStartDate": "2026-11-06", "PlannedEndDate": "2026-11-20"}
        orders = self.source([row], urls).open_orders(5)
        assert (orders[0].description, orders[0].quantity, orders[0].start) == ("RM-1001", Decimal("3500.000"), date(2026, 11, 6))
        assert "ProductionOrder?$filter=ProductionStatus eq 'R'&$orderby=PlannedStartDate,ProductionOrder&$top=5" in urls[0]


class TestOverview:
    def source(self):
        rows = [day(date(2026, 10, 20), good="150", scrap="10", target="170", planned="10", down="3"), day(date(2026, 9, 20), good="100")]
        return MockProductionSource(
            days=rows,
            downtimes=[DowntimeDay(date(2026, 10, 1), "CHANGEOVER", Decimal("30")), DowntimeDay(date(2026, 10, 2), "BREAKDOWN", Decimal("48"))],
            scraps=[ScrapDay(date(2026, 10, 1), "MACHINE_SETTING", Decimal("70"), "INR"), ScrapDay(date(2026, 10, 2), "OPERATOR_ERROR", Decimal("30"), "INR")],
        )

    def lines(self, *ids, source=None):
        from synapse_api.application.production_summary import GetProductionSummary

        return GetProductionSummary(source or self.source()).execute(TODAY, "INR", set(ids))

    def test_the_headline_compares_with_the_30_days_before(self):
        assert self.lines("prod-output") == ["Output over the last 30 days was ₹150, up 50.0% on the 30 days before."]

    def test_without_a_window_before_it_only_gives_the_value(self):
        source = MockProductionSource(days=[day(date(2026, 10, 20), good="150")])
        assert self.lines("prod-output", source=source) == ["Output over the last 30 days was ₹150."]

    def test_effectiveness_names_the_weakest_factor(self):
        line = self.lines("prod-output", "prod-oee")[1]
        assert line == "Equipment effectiveness is 62% over the last 30 days, held back most by availability."

    def test_downtime_and_scrap_sentences(self):
        assert self.lines("prod-output", "prod-scrap")[1] == "Machine setting caused the most scrap in the last 90 days: ₹70 (70% of scrapped output)."
        assert self.lines("prod-output", "prod-downtime")[1] == "Breakdown caused the most downtime in the last 90 days: 48 hours."

    def test_nothing_produced_says_nothing(self):
        assert self.lines("prod-output", source=MockProductionSource()) == []

    def test_a_board_with_sales_and_production_gets_both(self):
        from synapse_api.application.board_summary import GetBoardSummary
        from synapse_api.domain.entities.sales import DailySales
        from synapse_api.infrastructure.mock_sales_source import MockSalesSource

        sales = MockSalesSource([DailySales(date(2026, 11, 2), Decimal("300"), 1, "INR"), DailySales(date(2026, 10, 2), Decimal("200"), 1, "INR")])
        lines = GetBoardSummary(sales, Decimal(0), production=self.source()).execute(TODAY, "INR", {"sales-month", "prod-output", "prod-oee"})
        assert lines[0].startswith("Sales this month") and lines[1].startswith("Output over") and lines[2].startswith("Equipment effectiveness") and len(lines) == 3


class TestInTheCatalog:
    def test_each_id_is_listed_once_the_library_keeps_the_rest_and_production_is_real(self):
        from fastapi.testclient import TestClient
        from test_routes_totals import SECRET, TODAY as DAY, token_with
        from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

        from synapse_api.entrypoint.app import create_app
        from synapse_api.infrastructure.mock_sales_source import MockSalesSource
        from synapse_api.infrastructure.settings import Settings

        client = TestClient(create_app(MockSalesSource(), Settings(jwt_secret=SECRET, _env_file=None), lambda: DAY, production=MockProductionSource()))
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"]))
        ids = [e["id"] for e in client.get("/v1/synapse/catalog").json()["entries"]]
        assert len(ids) == len(set(ids)) == 50 and "exp-revenue" in ids and "fin-collections" in ids
        assert client.get("/v1/synapse/catalog/prod-output/data").json()["measure"] == "output"
        assert client.get("/v1/synapse/catalog/exp-revenue/data").json()["title"] == "Export revenue"
