import httpx
import pytest

from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import CatalogUnavailable
from sami_agents.infrastructure.settings import Settings
from sami_agents.infrastructure.synapse_catalog_source import SynapseCatalogSource

BODY = {
    "entries": [
        {"id": "sales-today", "title": "Sales today", "description": "Net sales today.", "category": "Sales", "widget": "KpiCard"},
        {"id": "top-customers", "title": "Top customers", "description": "Ranked.", "category": "Sales", "widget": "RankedList"},
    ]
}


def source_with(handler) -> SynapseCatalogSource:
    return SynapseCatalogSource(Settings(_env_file=None), httpx.MockTransport(handler))


class TestEntries:
    def test_forwards_the_users_cookie_and_maps_the_entries(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["cookie"] = request.headers["cookie"]
            return httpx.Response(200, json=BODY)

        entries = source_with(handler).entries("the-token")
        assert seen == {"url": "http://localhost:8004/v1/synapse/catalog", "cookie": "access_token=the-token"}
        assert entries == [
            CatalogEntry("sales-today", "Sales today", "Net sales today."),
            CatalogEntry("top-customers", "Top customers", "Ranked."),
        ]

    def test_uses_the_configured_synapse_url(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            return httpx.Response(200, json=BODY)

        SynapseCatalogSource(Settings(synapse_url="http://synapse.test:9", _env_file=None), httpx.MockTransport(handler)).entries("t")
        assert seen["url"] == "http://synapse.test:9/v1/synapse/catalog"


class TestUnavailable:
    @pytest.mark.parametrize("status", [401, 403, 500, 503])
    def test_any_other_status_is_unavailable(self, status):
        with pytest.raises(CatalogUnavailable):
            source_with(lambda request: httpx.Response(status)).entries("t")

    def test_a_connection_error_is_unavailable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        with pytest.raises(CatalogUnavailable):
            source_with(handler).entries("t")

    @pytest.mark.parametrize("body", [{}, {"entries": [{"id": "x"}]}, {"entries": "no"}])
    def test_an_unreadable_body_is_unavailable(self, body):
        with pytest.raises(CatalogUnavailable):
            source_with(lambda request: httpx.Response(200, json=body)).entries("t")
