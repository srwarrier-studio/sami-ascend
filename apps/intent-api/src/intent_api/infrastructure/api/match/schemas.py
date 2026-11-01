from pydantic import BaseModel, Field, field_validator

from intent_api.domain.entities.match import Match

CANNOT_ANSWER = "cannot_answer"


class MatchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)

    @field_validator("question")
    @classmethod
    def trimmed(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question is empty")
        return value


class SelectedScenario(BaseModel):
    id: str
    probability: float
    clause: str


class MatchResponse(BaseModel):
    problem: str | None
    reason: str | None
    domain: str | None
    domain_probability: float
    domain_scores: dict[str, float]
    offered: list[str]
    scenarios: list[SelectedScenario]
    did_you_mean: list[str]

    @classmethod
    def from_match(cls, result: Match) -> "MatchResponse":
        return cls(
            problem=None if result.answered else CANNOT_ANSWER,
            reason=result.reason,
            domain=result.domain,
            domain_probability=result.domain_probability,
            domain_scores=result.domain_scores,
            offered=list(result.offered),
            scenarios=[SelectedScenario(id=item.scenario, probability=item.probability, clause=item.clause) for item in result.selected],
            did_you_mean=list(result.did_you_mean),
        )
