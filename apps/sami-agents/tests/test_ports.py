import pytest

from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import CatalogUnavailable, RelevanceUnavailable
from sami_agents.infrastructure.mock_catalog_source import MockCatalogSource
from sami_agents.infrastructure.mock_relevance_checker import MockRelevanceChecker

ENTRY = CatalogEntry("sales-today", "Sales today", "Net sales invoiced today.")
OTHER = CatalogEntry("day-sales", "Day sales", "Net sales for each day.")


class TestMockRelevanceChecker:
    def test_scores_every_widget_as_relevant_by_default(self):
        assert MockRelevanceChecker().check("sales", ENTRY) == 1.0

    def test_scores_the_given_widgets_and_records_the_calls(self):
        checker = MockRelevanceChecker({"sales-today": 0.2}, default=0.9)
        assert checker.check("sales", ENTRY) == 0.2
        assert checker.check("sales", OTHER) == 0.9
        assert checker.calls == [("sales", "sales-today"), ("sales", "day-sales")]

    def test_becomes_unavailable_from_the_given_call(self):
        checker = MockRelevanceChecker(fail_from=1)
        checker.check("sales", ENTRY)
        with pytest.raises(RelevanceUnavailable):
            checker.check("sales", OTHER)


class TestMockCatalogSource:
    def test_lists_default_entries_and_records_the_token(self):
        source = MockCatalogSource()
        entries = source.entries("token-1")
        assert entries[0].id == "sales-today"
        assert source.tokens == ["token-1"]

    def test_lists_the_given_entries(self):
        assert MockCatalogSource([ENTRY]).entries("t") == [ENTRY]

    def test_can_be_unavailable(self):
        with pytest.raises(CatalogUnavailable):
            MockCatalogSource(unavailable=True).entries("t")
