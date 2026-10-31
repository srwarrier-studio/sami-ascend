from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Decision:
    choice: str
    confidence: float


@dataclass
class Case:
    intent: str | None = None
    metric: str | None = None
    direction: str | None = None
    month: date | None = None
    scope: str | None = None
    confidences: dict[str, float] = field(default_factory=dict)
    how_read: list[str] = field(default_factory=list)
