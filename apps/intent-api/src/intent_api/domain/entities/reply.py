from dataclasses import dataclass

from intent_api.domain.entities.answer import Answer
from intent_api.domain.entities.match import Match
from intent_api.domain.entities.period import Period


@dataclass(frozen=True)
class Reply:
    match: Match
    answers: tuple[Answer, ...] = ()
    reason: str | None = None
    periods: tuple[str, ...] = ()
    message: str | None = None
    read: tuple[Period, ...] = ()

    @property
    def answered(self) -> bool:
        return self.reason is None
