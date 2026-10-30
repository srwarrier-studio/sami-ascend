import pytest

from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import CatalogUnavailable, ModelUnavailable
from sami_agents.infrastructure.mock_catalog_source import MockCatalogSource
from sami_agents.infrastructure.mock_chat_model import MockChatModel

ENTRY = CatalogEntry("sales-today", "Sales today", "Net sales invoiced today.")


class TestMockChatModel:
    def test_returns_the_configured_ids_and_records_the_message(self):
        model = MockChatModel(["sales-today", "top-customers"])
        assert model.pick_widgets("show me sales", [ENTRY]) == ["sales-today", "top-customers"]
        assert model.messages == ["show me sales"]

    def test_picks_nothing_by_default(self):
        assert MockChatModel().pick_widgets("hi", [ENTRY]) == []

    def test_raises_the_configured_error(self):
        with pytest.raises(ModelUnavailable):
            MockChatModel(error=ModelUnavailable()).pick_widgets("hi", [ENTRY])

    def test_returned_list_is_a_copy(self):
        model = MockChatModel(["a"])
        model.pick_widgets("hi", [ENTRY]).append("b")
        assert model.pick_widgets("hi", [ENTRY]) == ["a"]


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
