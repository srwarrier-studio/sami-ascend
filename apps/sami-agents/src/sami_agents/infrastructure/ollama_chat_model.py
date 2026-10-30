import json

import httpx
from structured_logging import get_request_id

from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import InvalidModelAnswer, ModelUnavailable
from sami_agents.domain.gateways.chat_model import ChatModel
from sami_agents.infrastructure.settings import Settings

MAX_TOKENS = 200
MAX_PICKS = 8

INSTRUCTIONS = (
    "You choose dashboard widgets for a sales manager. "
    "Below is the list of available widgets, one per line as `id: title - description`. "
    "Pick the widgets that best answer the user's request, most relevant first. "
    "Answer only with JSON like {\"widgets\": [\"id\", \"id\"]} using ids from the list. "
    "If nothing fits, answer {\"widgets\": []}."
)


def widget_schema(catalog: list[CatalogEntry]) -> dict:
    return {
        "type": "object",
        "properties": {"widgets": {"type": "array", "maxItems": MAX_PICKS, "items": {"type": "string", "enum": [entry.id for entry in catalog]}}},
        "required": ["widgets"],
    }


class OllamaChatModel(ChatModel):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.model = settings.ollama_model
        self.client = httpx.Client(base_url=settings.ollama_url, timeout=settings.model_timeout_seconds, transport=transport)

    def pick_widgets(self, message: str, catalog: list[CatalogEntry]) -> list[str]:
        listing = "\n".join(f"{entry.id}: {entry.title} - {entry.description}" for entry in catalog)
        body = {
            "model": self.model,
            "stream": False,
            "format": widget_schema(catalog),
            "options": {"temperature": 0, "num_predict": MAX_TOKENS},
            "messages": [
                {"role": "system", "content": f"{INSTRUCTIONS}\n\nWidgets:\n{listing}"},
                {"role": "user", "content": message},
            ],
        }
        headers = {"X-Request-ID": request_id} if (request_id := get_request_id()) else {}
        try:
            response = self.client.post("/api/chat", json=body, headers=headers)
        except httpx.TransportError as error:
            raise ModelUnavailable(type(error).__name__) from error
        if response.status_code != 200:
            raise ModelUnavailable(f"unexpected status {response.status_code}")
        try:
            widgets = json.loads(response.json()["message"]["content"])["widgets"]
        except (ValueError, KeyError, TypeError) as error:
            raise InvalidModelAnswer("unreadable answer") from error
        if not isinstance(widgets, list) or not all(isinstance(widget, str) for widget in widgets):
            raise InvalidModelAnswer("widgets is not a list of ids")
        return widgets
