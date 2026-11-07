from datetime import date
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


class PeriodRead(BaseModel):
    label: str
    start: date
    end: date
    complete: bool
    note: str | None


class AnswerResponse(BaseModel):
    problem: str | None
    reason: str | None
    periods: list[str]
    message: str | None
    period_read: list[PeriodRead]
    reading: MatchResponse
    answers: list[AnswerItem]

    @classmethod
    def from_reply(cls, reply: Reply) -> "AnswerResponse":
        return cls(
            problem=None if reply.answered else CANNOT_ANSWER,
            reason=reply.reason,
            periods=list(reply.periods),
            message=reply.message,
            period_read=[PeriodRead(label=period.label, start=period.start, end=period.end, complete=period.complete, note=period.note) for period in reply.read],
            reading=MatchResponse.from_match(reply.match),
            answers=[AnswerItem(scenario=answer.scenario, blocks=[{"type": block.type, **block.data} for block in answer.blocks]) for answer in reply.answers],
        )
