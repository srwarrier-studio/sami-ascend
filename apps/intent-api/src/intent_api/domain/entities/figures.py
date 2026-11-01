from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class TrendPoint:
    year: int
    month: int
    amount: Decimal


@dataclass(frozen=True)
class MonthFigure:
    currency: str
    amount: Decimal
    change_percent: Decimal | None
    complete: bool
    trend: tuple[TrendPoint, ...]


@dataclass(frozen=True)
class Row:
    key: str
    name: str
    current: Decimal
    previous: Decimal


@dataclass(frozen=True)
class Comparison:
    currency: str
    current: Decimal
    previous: Decimal
    change: Decimal
    change_percent: Decimal | None
    rows: tuple[Row, ...]
    truncated: bool


@dataclass(frozen=True)
class Window:
    start: date
    end: date
    compare_start: date
    compare_end: date
