from datetime import date
from decimal import Decimal

import pytest

from synapse_api.application.combined_catalog import CombinedCatalog
from synapse_api.application.sales_widgets import SalesWidgetCatalog
from synapse_api.domain.errors import CatalogEntryNotFound
from synapse_api.infrastructure.mock_library_catalog import MockLibraryCatalog
from synapse_api.infrastructure.mock_sales_source import MockSalesSource

TODAY = date(2026, 10, 27)

REQUIRED = {
    "KpiCard": {"title", "value"},
    "GaugeChart": {"title", "value", "target"},
    "RankedList": {"title", "items"},
    "BarChart": {"title", "data"},
    "AreaChart": {"title", "data"},
    "LineChart": {"title", "data"},
    "StackedBarChart": {"title", "series"},
    "DonutChart": {"title", "slices"},
    "DataTable": {"title", "columns", "rows"},
    "HeatmapChart": {"title", "cells"},
    "CalendarHeatmapChart": {"title", "days"},
}


class TestMockLibrary:
    def test_lists_every_library_widget_in_its_domain(self):
        entries = MockLibraryCatalog().entries()
        assert len(entries) == 39
        assert {e.category for e in entries} == {"Finance", "Purchase", "Inventory", "Exports", "Production"}
        assert [e.id for e in entries][:2] == ["fin-receivables", "fin-collections"]

    def test_every_entry_has_the_props_its_widget_needs(self):
        catalog = MockLibraryCatalog()
        for entry in catalog.entries():
            props = catalog.data(entry.id, TODAY)
            assert REQUIRED[entry.widget] <= props.keys(), entry.id
            assert props["title"] == entry.title

    def test_unknown_id_is_not_found(self):
        with pytest.raises(CatalogEntryNotFound):
            MockLibraryCatalog().data("nope", TODAY)


class TestCombinedCatalog:
    catalog = CombinedCatalog(SalesWidgetCatalog(MockSalesSource(), Decimal(1000)), MockLibraryCatalog())

    def test_lists_sales_then_library_entries_without_repeats(self):
        ids = [e.id for e in self.catalog.entries()]
        assert len(ids) == len(set(ids)) == 11 + 39
        assert ids[0] == "sales-today" and ids[11] == "fin-receivables"

    def test_serves_data_from_the_catalog_that_owns_the_id(self):
        assert self.catalog.data("sales-today", TODAY)["measure"] == "sales"
        assert self.catalog.data("inv-low", TODAY)["value"] == 14

    def test_unknown_id_is_not_found(self):
        with pytest.raises(CatalogEntryNotFound):
            self.catalog.data("nope", TODAY)
