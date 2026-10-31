import httpx
from structured_logging import get_request_id

from sami_agents.domain.entities.case import Decision
from sami_agents.domain.errors import CaseModelUnavailable
from sami_agents.domain.gateways.case_model import CaseModel
from sami_agents.infrastructure.settings import Settings

CHECKPOINT = "typed-decisions"


class LayaCaseModel(CaseModel):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        headers = {"Authorization": f"Bearer {settings.laya_api_key}"} if settings.laya_api_key else {}
        self.client = httpx.Client(base_url=settings.laya_url, timeout=settings.laya_timeout_seconds, headers=headers, transport=transport)

    def decide(self, text: str, name: str, instructions: str, choices: dict[str, str]) -> Decision:
        body = {
            "state": {"request": text},
            "questions": {name: {"type": "choice", "instructions": instructions, "criteria": choices}},
            "model": CHECKPOINT,
        }
        headers = {"X-Request-ID": request_id} if (request_id := get_request_id()) else {}
        try:
            response = self.client.post("/v1/systemone", json=body, headers=headers)
        except httpx.TransportError as error:
            raise CaseModelUnavailable(type(error).__name__) from error
        if response.status_code != 200:
            raise CaseModelUnavailable(f"unexpected status {response.status_code}")
        try:
            probabilities = response.json()["answers"][name]["probabilities"]
            scored = {choice: float(probabilities[choice]) for choice in choices}
        except (ValueError, KeyError, TypeError) as error:
            raise CaseModelUnavailable("unreadable answer") from error
        best = max(scored, key=scored.get)
        return Decision(best, scored[best])
