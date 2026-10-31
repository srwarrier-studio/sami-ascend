import json

import httpx
from structured_logging import get_request_id

from sami_agents.domain.gateways.question_model import HeadlineRewriter, QuestionModel
from sami_agents.infrastructure.settings import Settings

READ_INSTRUCTIONS = (
    "Read a manager's question about why a business figure rose or fell in a month. Answer with JSON only, with the keys "
    '"metric" (one of: {metrics}), "direction" ("rise", "fall" or "change") and "month" (YYYY-MM). '
    "If the question does not ask that, answer {{}}."
)
REWRITE_INSTRUCTIONS = (
    "Rewrite the sentence in a friendlier way in one line. Keep every number, date and name exactly as given and add none."
)


class OllamaClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.model = settings.ollama_model
        self.client = httpx.Client(base_url=settings.ollama_url, timeout=settings.model_timeout_seconds, transport=transport)

    def chat(self, system: str, user: str, json_format: bool, tokens: int) -> str | None:
        body = {
            "model": self.model, "stream": False, "options": {"temperature": 0, "num_predict": tokens},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        if json_format:
            body["format"] = "json"
        headers = {"X-Request-ID": request_id} if (request_id := get_request_id()) else {}
        try:
            response = self.client.post("/api/chat", json=body, headers=headers)
            return str(response.json()["message"]["content"]) if response.status_code == 200 else None
        except (httpx.TransportError, ValueError, KeyError, TypeError):
            return None


class OllamaQuestionModel(QuestionModel):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.ollama = OllamaClient(settings, transport)

    def read(self, text: str, metrics: list[str]) -> dict | None:
        answer = self.ollama.chat(READ_INSTRUCTIONS.format(metrics=", ".join(metrics)), text, True, 80)
        try:
            data = json.loads(answer) if answer else None
        except ValueError:
            return None
        return data if isinstance(data, dict) else None


class OllamaHeadlineRewriter(HeadlineRewriter):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.ollama = OllamaClient(settings, transport)

    def rewrite(self, headline: str) -> str | None:
        return self.ollama.chat(REWRITE_INSTRUCTIONS, headline, False, 120)
