from datetime import date
from decimal import Decimal
from urllib.parse import unquote

import httpx
import pytest

from synapse_api.application.catalog import GetWidgetData, ListCatalog
from synapse_api.application.export_widgets import export_catalog
from synapse_api.domain.entities.exports import DestinationExport, ExportDay, ModeExport, TransitShipment
from synapse_api.infrastructure.butterfly_export_source import ButterflyExportSource
from synapse_api.infrastructure.mock_export_source import MockExportSource
from synapse_api.infrastructure.odata_reader import ODataReader

TODAY = date(2026, 10, 27)


def data(source: MockExportSource, entry_id: str, today: date = TODAY, currency: str = "INR", top: int = 5) -> dict:
    return GetWidgetData(export_catalog(source)).execute(entry_id, today, currency, top)


def day(d: date, count: int, amount: str, currency: str = "INR") -> ExportDay:
    return ExportDay(d, count, Decimal(amount), currency)


class TestList:
    def test_lists_the_seven_export_widgets_under_their_old_ids(self):
        entries = ListCatalog(export_catalog(MockExportSource())).execute()
        assert [e.id for e in entries] == ["exp-shipments", "exp-revenue", "exp-trend", "exp-destinations", "exp-modes", "exp-transit", "exp-calendar"]
        assert {e.category for e in entries} == {"Exports"}


class TestKpis:
    def source(self):
        return MockExportSource(days=[day(date(2026, 10, 2), 3, "300"), day(date(2026, 10, 20), 2, "200"), day(date(2026, 9, 2), 4, "250"), day(date(2026, 9, 29), 9, "999"), day(date(2026, 10, 2), 7, "777", "USD")])

    def test_revenue_compares_with_the_same_days_last_month_and_names_them(self):
        props = data(self.source(), "exp-revenue")
        assert props["value"] == 500.0 and props["delta"] == pytest.approx(1.0) and props["valueFormat"] == "currency"
        assert props["measure"] == "export revenue" and props["caption"] == "1–27 Oct vs 1–27 Sep"
        assert len(props["trend"]) == 6 and props["trend"][-1] == 500.0 and props["trend"][-2] == 1249.0

    def test_shipments_are_counted_with_the_number_format(self):
        props = data(self.source(), "exp-shipments")
        assert props["value"] == 5.0 and props["valueFormat"] == "number" and props["delta"] == pytest.approx(0.25) and props["measure"] == "shipments"

    def test_early_in_the_month_it_says_it_is_partial(self):
        props = data(MockExportSource(days=[day(date(2026, 11, 2), 1, "10")]), "exp-revenue", date(2026, 11, 3))
        assert props["note"] == "3 of 30 days so far" and props["partial"] is True


class TestTrend:
    def test_has_six_months_ending_this_one(self):
        props = data(MockExportSource(days=[day(date(2026, 10, 2), 1, "300"), day(date(2026, 10, 9), 1, "100"), day(date(2026, 6, 5), 1, "50"), day(date(2026, 4, 5), 1, "9")]), "exp-trend")
        assert [d["label"] for d in props["data"]] == ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
        assert [d["value"] for d in props["data"]] == [0.0, 50.0, 0.0, 0.0, 0.0, 400.0]


class TestDestinationsAndModes:
    def test_destinations_rank_by_value_over_90_days_and_leave_out_old_rows(self):
        source = MockExportSource(
            destinations=[
                DestinationExport(date(2026, 10, 2), "US", "United States", 3, Decimal("300"), "INR"),
                DestinationExport(date(2026, 9, 2), "US", "United States", 1, Decimal("100"), "INR"),
                DestinationExport(date(2026, 10, 3), "DE", "Germany", 1, Decimal("250"), "INR"),
                DestinationExport(date(2026, 1, 3), "JP", "Japan", 1, Decimal("999"), "INR"),
                DestinationExport(date(2026, 10, 3), "AE", "Emirates", 1, Decimal("9"), "USD"),
            ]
        )
        assert data(source, "exp-destinations")["items"] == [{"label": "United States", "value": 400.0}, {"label": "Germany", "value": 250.0}]

    def test_modes_are_named_and_zero_modes_dropped(self):
        source = MockExportSource(modes=[ModeExport(date(2026, 10, 2), "S", 5), ModeExport(date(2026, 10, 3), "A", 2), ModeExport(date(2026, 10, 3), "R", 0), ModeExport(date(2026, 1, 1), "R", 99)])
        assert data(source, "exp-modes")["slices"] == [{"label": "Sea", "value": 5}, {"label": "Air", "value": 2}]


class TestTransit:
    def test_lists_shipments_earliest_expected_arrival_first_and_marks_late_ones(self):
        source = MockExportSource(
            transit=[
                TransitShipment("2", "Germany", date(2026, 11, 5), Decimal("200"), "INR"),
                TransitShipment("1", "United States", date(2026, 10, 20), Decimal("100"), "INR"),
                TransitShipment("3", "Japan", date(2026, 11, 9), Decimal("50"), "USD"),
            ]
        )
        rows = data(source, "exp-transit")["rows"]
        assert rows == [
            {"shipment": "1", "destination": "United States", "status": "Late", "value": 100.0},
            {"shipment": "2", "destination": "Germany", "status": "In transit", "value": 200.0},
        ]


class TestCalendar:
    def test_has_a_point_per_day_with_shipments_within_a_year(self):
        source = MockExportSource(days=[day(date(2026, 10, 2), 3, "1"), day(date(2026, 10, 2), 2, "1"), day(date(2026, 10, 3), 0, "0"), day(date(2025, 9, 1), 5, "1"), day(date(2026, 5, 5), 4, "1", "USD")])
        assert data(source, "exp-calendar")["days"] == [{"date": "2026-10-02", "value": 5}]


class TestButterflySource:
    def source(self, rows, urls):
        def handler(request):
            urls.append(unquote(str(request.url)))
            return httpx.Response(200, json={"value": rows})

        return ButterflyExportSource(ODataReader("http://sap/export/", 5, httpx.MockTransport(handler)))

    def test_the_summaries_ask_for_the_range_and_company(self):
        urls = []
        start, end = date(2026, 10, 1), date(2026, 10, 31)
        row = {"ShipmentDate": "2026-10-02", "ShipmentCount": 4, "NetAmount": "400.00", "Currency": "INR"}
        result = self.source([row], urls).for_companies(("INA1",)).day_summaries(start, end)
        assert (result[0].count, result[0].amount) == (4, Decimal("400.00"))
        assert "ExportSummaryByDay?$filter=ShipmentDate ge 2026-10-01 and ShipmentDate le 2026-10-31 and (CompanyCode eq 'INA1')&$orderby=ShipmentDate,Currency,CompanyCode" in urls[0]
        destination = {"ShipmentDate": "2026-10-02", "Country": "US", "CountryName": None, "ShipmentCount": 1, "NetAmount": "5.00", "Currency": "INR"}
        mode = {"ShipmentDate": "2026-10-02", "TransportMode": "S", "ShipmentCount": 1}
        assert self.source([destination], urls).destination_summaries(start, end)[0].name == "US"
        assert self.source([mode], urls).mode_summaries(start, end)[0].mode == "S"
        assert "ExportSummaryByDestination?" in urls[1] and "ExportSummaryByMode?" in urls[2]

    def test_in_transit_reads_the_shipments_with_status_t_earliest_arrival_first(self):
        urls = []
        row = {"Shipment": "6000000001", "Country": "US", "CountryName": "United States", "ExpectedArrivalDate": "2026-11-05", "NetAmount": "99.00", "Currency": "INR"}
        shipments = self.source([row], urls).in_transit(5)
        assert (shipments[0].destination, shipments[0].expected) == ("United States", date(2026, 11, 5))
        assert "ExportShipment?$filter=ShipmentStatus eq 'T'&$orderby=ExpectedArrivalDate,Shipment&$top=5" in urls[0]


class TestOverview:
    def source(self):
        return MockExportSource(
            days=[day(date(2026, 10, 2), 3, "300"), day(date(2026, 9, 2), 2, "200")],
            destinations=[DestinationExport(date(2026, 10, 2), "US", "United States", 3, Decimal("300"), "INR"), DestinationExport(date(2026, 10, 3), "DE", "Germany", 1, Decimal("100"), "INR")],
            modes=[ModeExport(date(2026, 10, 2), "S", 3), ModeExport(date(2026, 10, 3), "A", 1)],
            transit=[TransitShipment("1", "US", date(2026, 10, 20), Decimal("1"), "INR"), TransitShipment("2", "DE", date(2026, 11, 5), Decimal("1"), "INR")],
        )

    def lines(self, *ids, source=None):
        from synapse_api.application.export_summary import GetExportSummary

        return GetExportSummary(source or self.source()).execute(TODAY, "INR", set(ids))

    def test_the_headline_counts_shipments_and_compares_with_the_same_days_last_month(self):
        assert self.lines("exp-shipments") == ["Exports this month are 3 shipments worth ₹300 (1–27 Oct), up 50.0% on 1–27 Sep."]

    def test_transit_destination_and_mode_sentences_each_need_their_widget(self):
        assert self.lines("exp-shipments", "exp-transit")[1] == "2 shipments are in transit, 1 of them past their expected arrival."
        assert self.lines("exp-destinations", "exp-shipments")[1] == "United States is the top destination over the last 90 days: ₹300 (75% of exports)."
        assert self.lines("exp-modes", "exp-shipments")[1] == "Sea carries 75% of shipments over the last 90 days."

    def test_nothing_exported_says_nothing(self):
        assert self.lines("exp-shipments", source=MockExportSource()) == []

    def test_a_board_with_sales_and_exports_gets_both_in_order(self):
        from synapse_api.application.board_summary import GetBoardSummary
        from synapse_api.domain.entities.sales import DailySales
        from synapse_api.infrastructure.mock_sales_source import MockSalesSource

        sales = MockSalesSource([DailySales(date(2026, 10, 2), Decimal("300"), 1, "INR"), DailySales(date(2026, 9, 2), Decimal("200"), 1, "INR")])
        lines = GetBoardSummary(sales, Decimal(0), exports=self.source()).execute(TODAY, "INR", {"sales-month", "exp-revenue", "exp-transit", "exp-modes"})
        assert lines[0].startswith("Sales this month") and lines[1].startswith("Exports this month") and lines[2].startswith("2 shipments are in transit") and len(lines) == 3


class TestInTheCatalog:
    def test_each_id_is_listed_once_exports_are_real_and_finance_cash_stays_mock(self):
        from fastapi.testclient import TestClient
        from test_routes_totals import SECRET, TODAY as DAY, token_with
        from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

        from synapse_api.entrypoint.app import create_app
        from synapse_api.infrastructure.mock_sales_source import MockSalesSource
        from synapse_api.infrastructure.settings import Settings

        client = TestClient(create_app(MockSalesSource(), Settings(jwt_secret=SECRET, _env_file=None), lambda: DAY, exports=MockExportSource()))
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"]))
        ids = [e["id"] for e in client.get("/v1/synapse/catalog").json()["entries"]]
        assert len(ids) == len(set(ids)) == 50 and "fin-collections" in ids
        assert client.get("/v1/synapse/catalog/exp-shipments/data").json()["measure"] == "shipments"
        assert client.get("/v1/synapse/catalog/fin-collections/data").json()["title"] == "Collections this month"
