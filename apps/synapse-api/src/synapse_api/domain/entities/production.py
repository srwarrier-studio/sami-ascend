from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ProductionDay:
    day: date
    planned_hours: Decimal
    downtime_hours: Decimal
    target: Decimal
    good: Decimal
    scrap: Decimal
    currency: str


@dataclass(frozen=True)
class DowntimeDay:
    day: date
    cause: str
    hours: Decimal


@dataclass(frozen=True)
class ScrapDay:
    day: date
    reason: str
    value: Decimal
    currency: str


@dataclass(frozen=True)
class LineShiftOutput:
    day: date
    line: str
    name: str
    shift: str
    good: Decimal
    currency: str


@dataclass(frozen=True)
class OpenOrder:
    order: str
    description: str
    quantity: Decimal
    start: date
    end: date
