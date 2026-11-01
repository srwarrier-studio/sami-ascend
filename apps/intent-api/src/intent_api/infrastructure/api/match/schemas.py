from pydantic import BaseModel, Field, field_validator


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
