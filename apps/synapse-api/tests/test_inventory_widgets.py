from datetime import date
from decimal import Decimal

import pytest

from synapse_api.application.catalog import GetWidgetData, ListCatalog
from synapse_api.application.inventory_widgets import inventory_catalog
from synapse_api.domain.entities.inventory import DayMovement, GroupStock, HourMovement, MonthValue, StatusStock, StockItem, WarehouseStock
from synapse_api.infrastructure.mock_inventory_source import MockInventorySource

TODAY = date(2026, 11, 3)


def data(source: MockInventorySource, entry_id: str, currency: str = "INR", top: int = 5) -> dict:
    return GetWidgetData(inventory_catalog(source)).execute(entry_id, TODAY, currency, top)


def item(material: str, quantity: str, level: str, status: str, last: date | None = date(2026, 10, 20), currency: str = "INR") -> StockItem:
    return StockItem(material, f"{material} item", Decimal(quantity), "KG", Decimal(level), status, last, currency)


def status(code: str, value: str, count: int, currency: str = "INR") -> StatusStock:
    return StatusStock(code, Decimal(value), count, currency)


class TestList:
    def test_lists_the_nine_inventory_widgets_under_their_old_ids(self):
        entries = ListCatalog(inventory_catalog(MockInventorySource())).execute()
        assert [e.id for e in entries] == ["inv-value", "inv-low", "inv-availability", "inv-warehouses", "inv-groups", "inv-slow", "inv-movement", "inv-reorder", "inv-heat"]
        assert {e.category for e in entries} == {"Inventory"}


class TestStockValue:
    def source(self, with_history=True):
        months = [MonthValue("2026-06", Decimal("800"), "INR"), MonthValue("2026-09", Decimal("900"), "INR"), MonthValue("2026-10", Decimal("1000"), "INR"), MonthValue("2026-11", Decimal("1100"), "INR")]
        return MockInventorySource(warehouses=[WarehouseStock("1000", "0001", "Raw", Decimal("600"), 3, "INR"), WarehouseStock("1000", "0002", "Finished", Decimal("500"), 3, "INR")], months=months if with_history else [])

    def test_is_the_stock_now_against_the_last_month_end(self):
        props = data(self.source(), "inv-value")
        assert props["value"] == 1100.0
        assert props["delta"] == pytest.approx(0.1)
        assert props["caption"] == "vs 31 Oct"
        assert props["trend"] == [800.0, 900.0, 1000.0, 1100.0]

    def test_without_a_last_month_end_there_is_no_delta(self):
        props = data(self.source(with_history=False), "inv-value")
        assert "delta" not in props and props["value"] == 1100.0

    def test_companies_in_the_same_month_are_added_up_and_other_currencies_left_out(self):
        source = MockInventorySource(months=[MonthValue("2026-10", Decimal("10"), "INR"), MonthValue("2026-10", Decimal("5"), "INR"), MonthValue("2026-10", Decimal("99"), "USD")])
        assert data(source, "inv-value")["trend"] == [15.0]


class TestItemsBelowReorder:
    def test_counts_low_and_zero_and_says_how_many_are_out(self):
        source = MockInventorySource(statuses=[status("O", "100", 30), status("L", "10", 3), status("Z", "0", 4), status("Z", "0", 9, "USD")])
        props = data(source, "inv-low")
        assert (props["value"], props["caption"]) == (7, "4 out of stock")

    def test_none_out_of_stock(self):
        assert data(MockInventorySource(statuses=[status("L", "10", 2)]), "inv-low")["caption"] == "none out of stock"


class TestAvailability:
    def test_is_the_share_of_rows_with_stock(self):
        props = data(MockInventorySource(statuses=[status("O", "1", 30), status("L", "1", 2), status("Z", "0", 4)]), "inv-availability")
        assert props["value"] == pytest.approx(32 / 36) and props["target"] == 1.0

    def test_no_stock_rows_is_zero(self):
        assert data(MockInventorySource(), "inv-availability")["value"] == 0.0


class TestWarehouses:
    def test_one_bar_per_location_named_without_the_plant_for_one_plant(self):
        source = MockInventorySource(warehouses=[WarehouseStock("1000", "0001", "Raw", Decimal("5"), 1, "INR"), WarehouseStock("1000", "0002", "Finished", Decimal("7"), 1, "INR")])
        assert data(source, "inv-warehouses")["data"] == [{"label": "Raw", "value": 5.0}, {"label": "Finished", "value": 7.0}]

    def test_the_plant_is_added_when_several_are_read(self):
        source = MockInventorySource(warehouses=[WarehouseStock("1000", "0001", "Raw", Decimal("5"), 1, "INR"), WarehouseStock("2000", "0001", "Raw", Decimal("7"), 1, "INR")])
        assert [d["label"] for d in data(source, "inv-warehouses")["data"]] == ["Raw (1000)", "Raw (2000)"]


class TestGroups:
    def test_shares_the_value_by_group_and_leaves_out_empty_ones(self):
        source = MockInventorySource(
            groups=[GroupStock("B", "Botanical", Decimal("30"), 2, "INR"), GroupStock("B", "Botanical", Decimal("20"), 1, "INR"), GroupStock("P", "Packing", Decimal("10"), 1, "INR"), GroupStock("Z", "Empty", Decimal("0"), 1, "INR")]
        )
        assert data(source, "inv-groups")["slices"] == [{"label": "Botanical", "value": 50.0}, {"label": "Packing", "value": 10.0}]


class TestSlow:
    def test_ranks_by_days_since_the_last_movement(self):
        source = MockInventorySource(items=[item("A", "5", "1", "O", date(2026, 10, 30)), item("B", "5", "1", "O", date(2026, 9, 1)), item("C", "0", "1", "Z", date(2026, 1, 1)), item("D", "5", "1", "O", None)])
        assert data(source, "inv-slow")["items"] == [{"label": "B item", "value": 63}, {"label": "A item", "value": 4}]

    def test_top_limits_the_rows(self):
        source = MockInventorySource(items=[item(str(n), "5", "1", "O", date(2026, 10, n)) for n in range(1, 9)])
        assert len(data(source, "inv-slow", top=3)["items"]) == 3


class TestMovement:
    def test_has_fourteen_days_with_zero_for_quiet_days_and_other_currencies_left_out(self):
        source = MockInventorySource(days=[DayMovement(date(2026, 11, 3), Decimal("10"), Decimal("4"), 3, "INR"), DayMovement(date(2026, 11, 3), Decimal("99"), Decimal("99"), 1, "USD"), DayMovement(date(2026, 10, 25), Decimal("7"), Decimal("0"), 1, "INR"), DayMovement(date(2026, 10, 1), Decimal("5"), Decimal("5"), 1, "INR")])
        props = data(source, "inv-movement")
        assert len(props["data"]) == len(props["compare"]) == 14
        assert props["data"][0]["label"] == "21 Oct" and props["data"][-1] == {"label": "3 Nov", "value": 10.0}
        assert props["compare"][-1]["value"] == 4.0 and props["data"][4]["value"] == 7.0 and props["data"][1]["value"] == 0.0
        assert (props["label"], props["compareLabel"]) == ("Receipts", "Issues")


class TestReorderList:
    def test_puts_out_of_stock_first_then_the_furthest_below(self):
        source = MockInventorySource(items=[item("A", "50", "100", "L"), item("B", "10", "100", "L"), item("C", "0", "100", "Z"), item("D", "500", "100", "O")])
        rows = data(source, "inv-reorder")["rows"]
        assert [r["material"] for r in rows] == ["C item", "B item", "A item"]
        assert rows[0] == {"material": "C item", "stock": 0.0, "level": 100.0, "status": "Out of stock"}
        assert rows[1]["status"] == "Low"

    def test_has_the_four_columns(self):
        assert [c["key"] for c in data(MockInventorySource(), "inv-reorder")["columns"]] == ["material", "stock", "level", "status"]


class TestHeat:
    def test_adds_up_movements_by_weekday_and_hour_and_only_lists_the_busy_ones(self):
        mon_a, mon_b, tue = date(2026, 11, 2), date(2026, 10, 26), date(2026, 11, 3)
        source = MockInventorySource(hours=[HourMovement(mon_a, 9, 4), HourMovement(mon_b, 9, 6), HourMovement(tue, 15, 2), HourMovement(date(2026, 1, 5), 9, 99)])
        cells = data(source, "inv-heat")["cells"]
        assert cells == [{"row": "Mon", "column": "9am", "value": 10}, {"row": "Tue", "column": "3pm", "value": 2}]


class TestOverview:
    def source(self):
        return MockInventorySource(
            statuses=[status("O", "1", 30), status("L", "1", 3), status("Z", "0", 4)],
            warehouses=[WarehouseStock("1000", "0001", "Raw", Decimal("1100"), 3, "INR")],
            groups=[GroupStock("B", "Botanical raw materials", Decimal("825"), 2, "INR"), GroupStock("P", "Packing", Decimal("275"), 1, "INR")],
            months=[MonthValue("2026-10", Decimal("1000"), "INR")],
            items=[item("A", "5", "1", "O", date(2026, 9, 1))],
        )

    def lines(self, *ids, source=None) -> list[str]:
        from synapse_api.application.inventory_summary import GetInventorySummary

        return GetInventorySummary(source or self.source()).execute(TODAY, "INR", set(ids))

    def test_the_headline_compares_with_the_last_month_end(self):
        assert self.lines("inv-value") == ["Stock is worth ₹1,100, up 10.0% on the end of Oct."]

    def test_without_history_it_only_says_the_value(self):
        source = MockInventorySource(warehouses=[WarehouseStock("1000", "0001", "Raw", Decimal("1100"), 3, "INR")])
        assert self.lines("inv-value", source=source) == ["Stock is worth ₹1,100."]

    def test_reorder_sentence_with_the_low_widget(self):
        assert self.lines("inv-value", "inv-low")[1] == "7 items are below their reorder level, 4 of them out of stock."

    def test_one_item_and_none(self):
        one = MockInventorySource(warehouses=[WarehouseStock("1", "1", "R", Decimal("5"), 1, "INR")], statuses=[status("Z", "0", 1)])
        assert self.lines("inv-low", source=one)[1] == "1 item is below its reorder level and is out of stock."
        none = MockInventorySource(warehouses=[WarehouseStock("1", "1", "R", Decimal("5"), 1, "INR")], statuses=[status("O", "5", 9)])
        assert len(self.lines("inv-low", source=none)) == 1

    def test_the_group_and_idle_sentences_each_need_their_widget(self):
        assert self.lines("inv-value", "inv-groups")[1] == "Botanical raw materials holds the most stock: ₹825 (75% of its value)."
        assert self.lines("inv-groups", "inv-slow")[1] == "Botanical raw materials holds the most stock: ₹825 (75% of its value)."
        slow_only = MockInventorySource(warehouses=[WarehouseStock("1", "1", "R", Decimal("5"), 1, "INR")], items=[item("A", "5", "1", "O", date(2026, 9, 1))])
        assert self.lines("inv-slow", source=slow_only)[1] == "A item has not moved for 63 days."

    def test_nothing_in_stock_says_nothing(self):
        assert self.lines("inv-value", source=MockInventorySource()) == []

    def test_a_board_with_sales_and_inventory_gets_both_in_order(self):
        from synapse_api.application.board_summary import GetBoardSummary
        from synapse_api.domain.entities.sales import DailySales
        from synapse_api.infrastructure.mock_sales_source import MockSalesSource

        sales = MockSalesSource([DailySales(date(2026, 11, 2), Decimal("300"), 1, "INR"), DailySales(date(2026, 10, 2), Decimal("200"), 1, "INR")])
        lines = GetBoardSummary(sales, Decimal(0), inventory=self.source()).execute(TODAY, "INR", {"sales-month", "inv-value", "inv-low", "inv-groups"})
        assert lines[0].startswith("Sales this month") and lines[1].startswith("Stock is worth") and len(lines) == 3
        assert lines[2].startswith("7 items are below")


class TestInTheCatalog:
    def client(self):
        from fastapi.testclient import TestClient
        from test_routes_totals import SECRET, TODAY as DAY, token_with
        from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

        from synapse_api.entrypoint.app import create_app
        from synapse_api.infrastructure.mock_sales_source import MockSalesSource
        from synapse_api.infrastructure.settings import Settings

        app = create_app(MockSalesSource(), Settings(jwt_secret=SECRET, _env_file=None), lambda: DAY, inventory=MockInventorySource())
        client = TestClient(app)
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"]))
        return client

    def test_each_id_is_listed_once_and_the_mock_library_keeps_the_rest(self):
        ids = [e["id"] for e in self.client().get("/v1/synapse/catalog").json()["entries"]]
        assert len(ids) == len(set(ids)) == 50
        assert "fin-collections" in ids and "inv-value" in ids

    def test_an_inventory_id_is_served_by_the_real_source_and_other_ids_by_the_library(self):
        client = self.client()
        assert client.get("/v1/synapse/catalog/inv-low/data").json()["measure"] == "items"
        assert client.get("/v1/synapse/catalog/fin-collections/data").json()["title"] == "Collections this month"

    def test_the_summary_follows_inventory_widgets(self):
        from test_routes_totals import TODAY as DAY  # noqa: F401

        assert self.client().get("/v1/synapse/summary?widgets=inv-value").json()["sentences"] == []
