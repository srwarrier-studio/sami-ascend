from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any


MAX_DAYS = 170


@dataclass(frozen=True)
class Window:
    start: date
    end: date
    compare_start: date
    compare_end: date

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    @classmethod
    def before(cls, start: date, end: date) -> "Window":
        length = (end - start).days + 1
        compare_end = start - timedelta(days=1)
        return cls(start, end, compare_end - timedelta(days=length - 1), compare_end)

    def widened_back(self, days: int) -> "Window":
        return Window.before(max(self.start - timedelta(days=days), self.end - timedelta(days=MAX_DAYS - 1)), self.end)

    def widened_forward(self, days: int, today: date) -> "Window":
        end = min(self.end + timedelta(days=days), self.start + timedelta(days=MAX_DAYS - 1), max(today, self.end))
        return Window.before(self.start, end)

    def span(self, pad_days: int) -> tuple[date, date]:
        return min(self.start, self.compare_start) - timedelta(days=pad_days), self.end + timedelta(days=pad_days)


@dataclass(frozen=True)
class MemberChange:
    current: Decimal
    previous: Decimal
    change_percent: Decimal | None
    volume_effect: Decimal | None = None
    price_effect: Decimal | None = None


@dataclass(frozen=True)
class Hit:
    kind: str
    at: date | None
    numbers: dict[str, Any]
    rows: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class Start:
    node: str
    key: str
    key_field: str | None = None


@dataclass(frozen=True)
class Step:
    node: str
    edge: str | None
    lookup_field: str
    keys: tuple[str, ...]
    kind: str
    at: date | None
    numbers: dict[str, Any]
    rows: list[dict]
    label: str = ""


@dataclass(frozen=True)
class Related:
    node: str
    field: str
    key: str
    rows: int


@dataclass
class WalkResult:
    paths: list[tuple[Step, ...]] = field(default_factory=list)
    related: list[Related] = field(default_factory=list)
    truncated: bool = False
