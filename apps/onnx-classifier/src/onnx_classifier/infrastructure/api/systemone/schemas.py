from typing import Literal

from pydantic import BaseModel, Field


class ChoiceQuestion(BaseModel):
    type: Literal["choice"]
    instructions: str = ""
    criteria: dict[str, str] = Field(min_length=1)


class SystemOneRequest(BaseModel):
    state: dict[str, str]
    questions: dict[str, ChoiceQuestion] = Field(min_length=1)
    model: str | None = None


class ChoiceAnswer(BaseModel):
    probabilities: dict[str, float]


class SystemOneResponse(BaseModel):
    answers: dict[str, ChoiceAnswer]
