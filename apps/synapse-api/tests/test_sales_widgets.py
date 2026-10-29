from datetime import date, timedelta
from decimal import Decimal

import pytest

from synapse_api.application.catalog import GetWidgetData, ListCatalog
from synapse_api.application.sales_widgets import SalesWidgetCatalog
from synapse_api.domain.entities.sales import CustomerSales, DailySales, HighValueOrder, MaterialSales
from synapse_api.domain.errors import CatalogEntryNotFound
from synapse_api.infrastructure.mock_sales_source import MockSalesSource

TODAY = date(2026, 10, 27)


def day(d: date, amount: str, count: int = 1, currency: str = "INR") -> DailySales:
    return DailySales(d, Decimal(amount), count, currency)


def make_catalog(**rows) -> SalesWidgetCatalog:
    return SalesWidgetCatalog(MockSalesSource(**rows))


def data(catalog: SalesWidgetCatalog, entry_id: str) -> dict:
    return GetWidgetData(catalog).execute(entry_id, TODAY)


class TestCatalogList:
    def test_lists_the_sales_entries_with_widget_names(self):
        entries = ListCatalog(make_catalog()).execute()
        ids = [e.id for e in entries]
        assert ids[:3] == ["sales-today", "sales-month", "sales-year"]
        assert {e.id: e.widget for e in entries}["top-customers"] == "RankedList"
        assert {e.id: e.category for e in entries}["top-materials"] == "Inventory"

    def test_unknown_entry_is_not_found(self):
        with pytest.raises(CatalogEntryNotFound):
            data(make_catalog(), "nope")


class TestSalesKpis:
    def test_today_compares_with_yesterday_and_trends_over_seven_days(self):
        catalog = make_catalog(daily=[day(TODAY, "120"), day(TODAY - timedelta(days=1), "100"), day(TODAY - timedelta(days=6), "50")])
        props = data(catalog, "sales-today")
        assert props["value"] == 120.0
        assert props["delta"] == pytest.approx(0.2)
        assert props["trend"] == [50.0, 0.0, 0.0, 0.0, 0.0, 100.0, 120.0]
        assert props["caption"] == "vs yesterday"

    def test_month_compares_with_the_same_days_last_month(self):
        catalog = make_catalog(daily=[day(date(2026, 10, 2), "300"), day(date(2026, 9, 2), "200"), day(date(2026, 9, 28), "999")])
        props = data(catalog, "sales-month")
        assert props["value"] == 300.0
        assert props["delta"] == pytest.approx(0.5)

    def test_year_compares_with_the_same_period_last_year(self):
        catalog = make_catalog(daily=[day(date(2026, 3, 1), "400"), day(date(2025, 3, 1), "200"), day(date(2025, 12, 1), "999")])
        assert data(catalog, "sales-year")["delta"] == pytest.approx(1.0)

    def test_no_delta_when_there_was_nothing_before(self):
        props = data(make_catalog(daily=[day(TODAY, "10")]), "sales-today")
        assert "delta" not in props

    def test_only_inr_is_counted(self):
        props = data(make_catalog(daily=[day(TODAY, "10"), day(TODAY, "999", currency="USD")]), "sales-today")
        assert props["value"] == 10.0

    def test_orders_this_month_counts_orders(self):
        props = data(make_catalog(daily=[day(date(2026, 10, 1), "1", count=4), day(TODAY, "1", count=3)]), "orders-month")
        assert props == {"title": "Orders this month", "measure": "orders", "value": 7, "caption": "since the 1st"}


class TestSalesCharts:
    def test_month_on_month_has_twelve_labelled_months(self):
        props = data(make_catalog(daily=[day(date(2026, 10, 3), "70")]), "month-on-month")
        assert [p["label"] for p in props["data"]][-2:] == ["Sep", "Oct"]
        assert len(props["data"]) == 12
        assert props["data"][-1]["value"] == 70.0

    def test_top_customers_and_materials_are_ranked_lists(self):
        customers = [CustomerSales("1", "Northwind", date(2026, 10, 5), Decimal("50"), 1, "INR"), CustomerSales("2", "Harbor", date(2026, 10, 6), Decimal("80"), 1, "INR")]
        materials = [MaterialSales("M1", "Rebar", date(2026, 10, 5), Decimal("1"), "EA", Decimal("20"), "INR")]
        catalog = make_catalog(customers=customers, materials=materials)
        assert data(catalog, "top-customers")["items"] == [{"label": "Harbor", "value": 80.0}, {"label": "Northwind", "value": 50.0}]
        assert data(catalog, "top-materials")["items"] == [{"label": "Rebar", "value": 20.0}]

    def test_high_value_orders_show_status_names(self):
        orders = [HighValueOrder("0000012001", "Northwind", TODAY, Decimal("150000"), "INR", "B")]
        row = data(make_catalog(orders=orders), "high-value-sales")["rows"][0]
        assert row == {"order": "0000012001", "customer": "Northwind", "status": "In process", "amount": 150000.0}
