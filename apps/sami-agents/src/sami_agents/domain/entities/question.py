from dataclasses import dataclass
from datetime import date

from sami_agents.domain.entities.case import Case


@dataclass(frozen=True)
class Question:
    metric: str
    direction: str
    month: date
    intent: str = "why"


@dataclass(frozen=True)
class ReadResult:
    question: Question | None
    problem: str | None = None
    case: Case | None = None
