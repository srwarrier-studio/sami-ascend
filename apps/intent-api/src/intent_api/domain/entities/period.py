from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Period:
    kind: str
    year: int
    month: int | None
    start: date
    end: date
    complete: bool
    label: str
