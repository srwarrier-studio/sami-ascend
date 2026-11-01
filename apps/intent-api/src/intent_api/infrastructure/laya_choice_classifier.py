import httpx
from structured_logging import get_request_id

from intent_api.domain.entities.decision import Decision
from intent_api.domain.errors import ClassifierUnavailable
from intent_api.domain.gateways.choice_classifier import ChoiceClassifier
from intent_api.infrastructure.settings import Settings

QUESTION = "choice"


class LayaChoiceClassifier(ChoiceClassifier):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        headers = {"Authorization": f"Bearer {settings.laya_api_key}"} if settings.laya_api_key else {}
        self.model = settings.laya_model
        self.client = httpx.Client(base_url=settings.laya_url, timeout=settings.laya_timeout_seconds, headers=headers, transport=transport)

    def choose(self, text: str, instructions: str, choices: dict[str, str]) -> Decision:
        body = {
            "state": {"question": text},
            "questions": {QUESTION: {"type": "choice", "instructions": instructions, "criteria": choices}},
            "model": self.model,
        }
        headers = {"X-Request-ID": request_id} if (request_id := get_request_id()) else {}
        try:
            response = self.client.post("/v1/systemone", json=body, headers=headers)
        except httpx.TransportError as error:
            raise ClassifierUnavailable(type(error).__name__) from error
        if response.status_code != 200:
            raise ClassifierUnavailable(f"unexpected status {response.status_code}")
        try:
            probabilities = response.json()["answers"][QUESTION]["probabilities"]
            scored = {choice: float(probabilities[choice]) for choice in choices}
        except (ValueError, KeyError, TypeError) as error:
            raise ClassifierUnavailable("unreadable answer") from error
        best = max(scored, key=scored.get)
        return Decision(best, scored[best])
