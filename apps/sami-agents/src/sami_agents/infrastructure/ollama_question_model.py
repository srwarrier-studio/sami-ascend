import json

import httpx
from structured_logging import get_request_id

from sami_agents.domain.gateways.question_model import LineRewriter, QuestionModel
from sami_agents.infrastructure.settings import Settings

READ_INSTRUCTIONS = (
    "Read a manager's question about why a business figure rose or fell in a month. Answer with JSON only, with the keys "
    '"metric" (one of: {metrics}), "direction" ("rise", "fall" or "change") and "month" (YYYY-MM). '
    "If the question does not ask that, answer {{}}."
)
TONES = {"executive": "a concise, professional tone for senior management", "friendly": "a warm, conversational tone"}
REWRITE_RULES = """You rewrite ONE sentence from a business report in {tone}.
Rules:
1. Keep every number, percentage, date, name and code exactly as written and in the same order. Do not round, convert or respell anything.
2. Keep the meaning exactly. "X% of the change" is that item's share of the whole change: never write "X% change". The amount in brackets after "fell 15.4%" is how much was lost: never write "to INR".
3. Keep every "no", "not" and "nothing". "and behind that" means the next thing lies behind the previous one: keep that phrase, never turn it into a plain "and" list.
4. Add no facts, reasons or words such as "price" that are not in the sentence. Drop nothing.
5. Reply with the rewritten sentence only: one line, no quotes, no markup."""
EXAMPLES = {
    "executive": [
        ("Zenith Corp fell 40.0% (INR 120,000), 55.5% of the change.", "Zenith Corp fell 40.0% (INR 120,000), accounting for 55.5% of the change."),
        ("This coincided with order 77 being 5 days late (due 2026-03-01, done 2026-03-06), and behind that delivery 99 being 4 days late (due 2026-02-20, done 2026-02-24).", "This coincided with order 77 running 5 days late (due 2026-03-01, done 2026-03-06), and behind that delivery 99 running 4 days late (due 2026-02-20, done 2026-02-24)."),
        ("Nothing unusual was found behind this month.", "No unusual cause was found behind this month."),
    ],
    "friendly": [
        ("Zenith Corp fell 40.0% (INR 120,000), 55.5% of the change.", "Zenith Corp dropped 40.0% (INR 120,000), and that is 55.5% of the change."),
        ("This coincided with order 77 being 5 days late (due 2026-03-01, done 2026-03-06), and behind that delivery 99 being 4 days late (due 2026-02-20, done 2026-02-24).", "This lined up with order 77 being 5 days late (due 2026-03-01, done 2026-03-06), and behind that delivery 99 being 4 days late (due 2026-02-20, done 2026-02-24)."),
        ("Nothing unusual was found behind this month.", "Nothing unusual turned up behind this month."),
    ],
}


class OllamaClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.model = settings.ollama_model
        self.client = httpx.Client(base_url=settings.ollama_url, timeout=settings.model_timeout_seconds, transport=transport)

    def chat(self, system: str, user: str, json_format: bool, tokens: int, examples: list[tuple[str, str]] | None = None) -> str | None:
        shots = [message for asked, answered in examples or [] for message in ({"role": "user", "content": asked}, {"role": "assistant", "content": answered})]
        body = {
            "model": self.model, "stream": False, "options": {"temperature": 0, "num_predict": tokens},
            "messages": [{"role": "system", "content": system}, *shots, {"role": "user", "content": user}],
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


class OllamaLineRewriter(LineRewriter):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.ollama = OllamaClient(settings, transport)

    def rewrite(self, line: str, tone: str) -> str | None:
        if tone not in TONES:
            return None
        return self.ollama.chat(REWRITE_RULES.format(tone=TONES[tone]), line, False, 160, EXAMPLES[tone])
