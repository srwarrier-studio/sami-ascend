import httpx
from structured_logging import get_request_id

from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import RelevanceUnavailable
from sami_agents.domain.gateways.relevance_checker import RelevanceChecker
from sami_agents.infrastructure.settings import Settings

CHECKPOINT = "typed-decisions"
QUESTION = {
    "fit": {
        "type": "choice",
        "instructions": "Would this widget help answer the request?",
        "criteria": {
            "yes": "the widget directly answers the request",
            "no": "the widget is about something else",
        },
    }
}


class LayaRelevanceChecker(RelevanceChecker):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        headers = {"Authorization": f"Bearer {settings.laya_api_key}"} if settings.laya_api_key else {}
        self.client = httpx.Client(base_url=settings.laya_url, timeout=settings.laya_timeout_seconds, headers=headers, transport=transport)

    def check(self, message: str, entry: CatalogEntry) -> float:
        body = {
            "state": {"request": message, "widget": f"{entry.title} - {entry.description}"},
            "questions": QUESTION,
            "model": CHECKPOINT,
        }
        headers = {"X-Request-ID": request_id} if (request_id := get_request_id()) else {}
        try:
            response = self.client.post("/v1/systemone", json=body, headers=headers)
        except httpx.TransportError as error:
            raise RelevanceUnavailable(type(error).__name__) from error
        if response.status_code != 200:
            raise RelevanceUnavailable(f"unexpected status {response.status_code}")
        try:
            return float(response.json()["answers"]["fit"]["probabilities"]["yes"])
        except (ValueError, KeyError, TypeError) as error:
            raise RelevanceUnavailable("unreadable answer") from error
