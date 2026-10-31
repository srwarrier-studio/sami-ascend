import httpx
from structured_logging import get_request_id

from sami_agents.domain.errors import ReplyUnavailable
from sami_agents.domain.gateways.reply_writer import ReplyWriter
from sami_agents.infrastructure.settings import Settings

MAX_TOKENS = 60
INSTRUCTIONS = (
    "You are the voice of a sales dashboard. Write exactly one short, friendly sentence of at most 25 words "
    "telling the manager which widgets you are showing for their request. Mention only the widget titles you are given. "
    "Do not use numbers, lists, markdown or quotes, and do not make up any figures."
)


class OllamaReplyWriter(ReplyWriter):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.model = settings.ollama_model
        self.client = httpx.Client(base_url=settings.ollama_url, timeout=settings.model_timeout_seconds, transport=transport)

    def write(self, message: str, titles: list[str], board_name: str | None) -> str:
        shown = f"A board called {board_name} with these widgets" if board_name else "These widgets"
        body = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": 0, "num_predict": MAX_TOKENS},
            "messages": [
                {"role": "system", "content": INSTRUCTIONS},
                {"role": "user", "content": f"Request: {message}\n{shown}: {', '.join(titles)}"},
            ],
        }
        headers = {"X-Request-ID": request_id} if (request_id := get_request_id()) else {}
        try:
            response = self.client.post("/api/chat", json=body, headers=headers)
        except httpx.TransportError as error:
            raise ReplyUnavailable(type(error).__name__) from error
        if response.status_code != 200:
            raise ReplyUnavailable(f"unexpected status {response.status_code}")
        try:
            return str(response.json()["message"]["content"])
        except (ValueError, KeyError, TypeError) as error:
            raise ReplyUnavailable("unreadable answer") from error
