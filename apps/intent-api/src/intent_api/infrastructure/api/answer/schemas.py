from typing import Literal

from pydantic import BaseModel

from intent_api.domain.entities.reply import Reply
from intent_api.infrastructure.api.match.schemas import CANNOT_ANSWER, MatchRequest, MatchResponse

COMPANIES = ("all", "sabinsa", "neutraceuticals", "organica")


class AnswerRequest(MatchRequest):
    company: Literal["all", "sabinsa", "neutraceuticals", "organica"] = "all"


class AnswerItem(BaseModel):
    scenario: str
    blocks: list[dict]


class AnswerResponse(BaseModel):
    problem: str | None
    reason: str | None
    periods: list[str]
    reading: MatchResponse
    answers: list[AnswerItem]

    @classmethod
    def from_reply(cls, reply: Reply) -> "AnswerResponse":
        return cls(
            problem=None if reply.answered else CANNOT_ANSWER,
            reason=reply.reason,
            periods=list(reply.periods),
            reading=MatchResponse.from_match(reply.match),
            answers=[AnswerItem(scenario=answer.scenario, blocks=[{"type": block.type, **block.data} for block in answer.blocks]) for answer in reply.answers],
        )
