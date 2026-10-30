import httpx
from structured_logging import get_request_id
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import CatalogUnavailable
from sami_agents.domain.gateways.catalog_source import CatalogSource
from sami_agents.infrastructure.settings import Settings


class SynapseCatalogSource(CatalogSource):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.client = httpx.Client(base_url=settings.synapse_url, timeout=settings.model_timeout_seconds, transport=transport)

    def entries(self, access_token: str) -> list[CatalogEntry]:
        headers = {"Cookie": f"{ACCESS_TOKEN_COOKIE}={access_token}"}
        if request_id := get_request_id():
            headers["X-Request-ID"] = request_id
        try:
            response = self.client.get("/v1/synapse/catalog", headers=headers)
        except httpx.TransportError as error:
            raise CatalogUnavailable(type(error).__name__) from error
        if response.status_code != 200:
            raise CatalogUnavailable(f"unexpected status {response.status_code}")
        try:
            return [CatalogEntry(row["id"], row["title"], row["description"]) for row in response.json()["entries"]]
        except (ValueError, KeyError, TypeError) as error:
            raise CatalogUnavailable("unreadable body") from error
