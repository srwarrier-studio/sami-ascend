from datetime import date
from decimal import Decimal

import pytest

from synapse_api.application.catalog import GetWidgetData, ListCatalog
from synapse_api.application.purchase_widgets import purchase_catalog
from synapse_api.domain.entities.purchases import DailyPurchases, PurchaseItem, SupplierPurchases
from synapse_api.infrastructure.mock_purchase_source import MockPurchaseSource

TODAY = date(2026, 10, 27)


def day(d: date, amount: str, currency: str = "INR") -> DailyPurchases:
    return DailyPurchases(d, Decimal(amount), 1, currency)


def supplier(code: str, name: str, d: date, amount: str, currency: str = "INR") -> SupplierPurchases:
    return SupplierPurchases(code, name, d, Decimal(amount), 1, currency)


def item(order: str, ordered: date, promised: date, actual: date | None, status: str = "D", name: str = "Pack-Rite", amount: str = "100", currency: str = "INR") -> PurchaseItem:
    return PurchaseItem(order, "00010", name, ordered, promised, actual, Decimal(amount), currency, status)


def data(source: MockPurchaseSource, entry_id: str, today: date = TODAY, currency: str = "INR", top: int = 5) -> dict:
    return GetWidgetData(purchase_catalog(source)).execute(entry_id, today, currency, top)


class TestList:
    def test_lists_the_purchase_widgets_under_their_old_ids(self):
        entries = ListCatalog(purchase_catalog(MockPurchaseSource())).execute()
        assert [e.id for e in entries] == ["pur-spend", "pur-open", "pur-trend", "pur-vendors", "pur-recent", "pur-ontime", "pur-categories", "pur-by-category-month"]
        assert {e.category for e in entries} == {"Purchase"}


class TestSpend:
    def test_compares_with_the_same_days_last_month_and_names_them(self):
        source = MockPurchaseSource(daily=[day(date(2026, 10, 2), "300"), day(date(2026, 9, 2), "200"), day(date(2026, 9, 29), "999")])
        props = data(source, "pur-spend")
        assert props["value"] == 300.0
        assert props["delta"] == pytest.approx(0.5)
        assert props["measure"] == "purchases"
        assert props["caption"] == "1–27 Oct vs 1–27 Sep"
        assert "partial" not in props

    def test_early_in_the_month_it_says_it_is_partial(self):
        props = data(MockPurchaseSource(daily=[day(date(2026, 11, 2), "10")]), "pur-spend", date(2026, 11, 3))
        assert props["note"] == "3 of 30 days so far"
        assert props["partial"] is True

    def test_only_the_asked_currency_is_counted(self):
        props = data(MockPurchaseSource(daily=[day(date(2026, 10, 2), "10"), day(date(2026, 10, 2), "99", "USD")]), "pur-spend")
        assert props["value"] == 10.0

    def test_the_trend_has_six_months(self):
        assert len(data(MockPurchaseSource(), "pur-spend")["trend"]) == 6


class TestOpenOrders:
    def test_counts_open_items_only(self):
        items = [item("1", date(2026, 10, 1), date(2026, 11, 1), None, "O"), item("2", date(2026, 10, 1), date(2026, 11, 1), None, "X"), item("3", date(2026, 10, 1), date(2026, 10, 5), date(2026, 10, 5), "D")]
        assert data(MockPurchaseSource(items=items), "pur-open")["value"] == 1


class TestTrend:
    def test_has_twelve_months_ending_this_one(self):
        props = data(MockPurchaseSource(daily=[day(date(2026, 10, 2), "300"), day(date(2025, 11, 2), "50"), day(date(2025, 10, 2), "999")]), "pur-trend")
        assert [point["label"] for point in props["data"]][0] == "Nov"
        assert len(props["data"]) == 12
        assert props["data"][-1] == {"label": "Oct", "value": 300.0}
        assert props["data"][0]["value"] == 50.0


class TestVendors:
    def test_ranks_suppliers_this_month_and_adds_their_days(self):
        source = MockPurchaseSource(
            suppliers=[supplier("1", "Pack-Rite", date(2026, 10, 2), "100"), supplier("1", "Pack-Rite", date(2026, 10, 9), "250"), supplier("2", "Malnad", date(2026, 10, 3), "300"), supplier("3", "Old", date(2026, 9, 30), "9999")]
        )
        assert data(source, "pur-vendors")["items"] == [{"label": "Pack-Rite", "value": 350.0}, {"label": "Malnad", "value": 300.0}]

    def test_top_limits_the_rows(self):
        source = MockPurchaseSource(suppliers=[supplier(str(n), f"S{n}", date(2026, 10, 2), str(n)) for n in range(1, 9)])
        assert len(data(source, "pur-vendors", top=3)["items"]) == 3


class TestRecent:
    def test_lists_the_latest_items_with_their_status_and_leaves_cancelled_out(self):
        items = [item("1", date(2026, 10, 1), date(2026, 10, 9), None, "O", "Pack-Rite", "560"), item("2", date(2026, 10, 5), date(2026, 10, 9), date(2026, 10, 8), "D", "Malnad", "310"), item("3", date(2026, 10, 6), date(2026, 10, 9), None, "X")]
        rows = data(MockPurchaseSource(items=items), "pur-recent")["rows"]
        assert rows == [
            {"po": "2/00010", "vendor": "Malnad", "status": "Delivered", "amount": 310.0},
            {"po": "1/00010", "vendor": "Pack-Rite", "status": "Open", "amount": 560.0},
        ]


class TestOnTime:
    def test_counts_delivered_by_the_promised_date_and_not_yet_delivered_as_late(self):
        items = [
            item("1", date(2026, 9, 1), date(2026, 10, 1), date(2026, 10, 1)),
            item("2", date(2026, 9, 1), date(2026, 10, 2), date(2026, 10, 1)),
            item("3", date(2026, 9, 1), date(2026, 10, 3), date(2026, 10, 9)),
            item("4", date(2026, 9, 1), date(2026, 10, 4), None, "O"),
            item("5", date(2026, 9, 1), date(2026, 12, 1), None, "O"),
            item("6", date(2025, 1, 1), date(2025, 2, 1), date(2025, 2, 1)),
        ]
        props = data(MockPurchaseSource(items=items), "pur-ontime")
        assert props["value"] == 0.5
        assert props["target"] == 1.0
        assert props["caption"] == "last 90 days"

    def test_nothing_due_says_so(self):
        props = data(MockPurchaseSource(), "pur-ontime")
        assert (props["value"], props["caption"]) == (0.0, "nothing due in 90 days")


def group(code: str, name: str, d: date, amount: str, currency: str = "INR"):
    from synapse_api.domain.entities.purchases import GroupPurchases

    return GroupPurchases(code, name, d, Decimal(amount), 1, currency)


class TestCategories:
    def source(self):
        return MockPurchaseSource(
            groups=[
                group("B", "Botanical", date(2026, 10, 24), "700"),
                group("B", "Botanical", date(2026, 9, 24), "300"),
                group("P", "Packing", date(2026, 9, 24), "200"),
                group("B", "Botanical", date(2026, 7, 24), "9999"),
                group("P", "Packing", date(2026, 10, 24), "50", "USD"),
                group("Z", "Empty", date(2026, 10, 24), "0"),
            ]
        )

    def test_the_donut_shares_the_last_three_months_biggest_first(self):
        slices = data(self.source(), "pur-categories")["slices"]
        assert slices == [{"label": "Botanical", "value": 1000.0}, {"label": "Packing", "value": 200.0}]

    def test_the_stacked_chart_has_six_months_ending_this_one_and_zeros_for_quiet_ones(self):
        props = data(self.source(), "pur-by-category-month")
        assert [p["label"] for p in props["series"][0]["data"]] == ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
        series = {s["name"]: [p["value"] for p in s["data"]] for s in props["series"]}
        assert series["Botanical"] == [0.0, 0.0, 9999.0, 0.0, 300.0, 700.0]
        assert series["Packing"] == [0.0, 0.0, 0.0, 0.0, 200.0, 0.0] and "Empty" not in series
        assert props["valueFormat"] == "currency"

    def test_no_groups_gives_empty_widgets(self):
        assert data(MockPurchaseSource(), "pur-categories")["slices"] == []
        assert data(MockPurchaseSource(), "pur-by-category-month")["series"] == []


class TestCategoryOverview:
    def lines(self, *ids):
        from synapse_api.application.purchase_summary import GetPurchaseSummary

        source = TestCategories().source()
        source.daily = [day(date(2026, 10, 2), "10")]
        return GetPurchaseSummary(source).execute(TODAY, "INR", set(ids))

    def test_names_the_biggest_category(self):
        assert self.lines("pur-spend", "pur-categories")[1] == "Botanical is the biggest category over the last 3 months: ₹1,000 (83% of purchases)."

    def test_the_cap_of_two_per_topic_applies_in_the_board_summary(self):
        from synapse_api.application.board_summary import GetBoardSummary
        from synapse_api.infrastructure.mock_sales_source import MockSalesSource

        source = TestCategories().source()
        source.daily = [day(date(2026, 10, 2), "10")]
        lines = GetBoardSummary(MockSalesSource(), Decimal(0), purchases=source).execute(TODAY, "INR", {"pur-spend", "pur-categories", "pur-vendors"})
        assert len(lines) == 2
