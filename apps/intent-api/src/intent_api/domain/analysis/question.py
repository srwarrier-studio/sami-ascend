from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Question:
    metric: str
    direction: str
    month: date
    intent: str = "why"
    currency: str | None = None
