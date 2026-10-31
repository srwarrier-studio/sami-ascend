from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ChangeRow:
    key: str
    name: str
    current: Decimal
    previous: Decimal
    change: Decimal
    share_of_change_percent: Decimal | None
    unit: str | None = None
    quantity_current: Decimal | None = None
    quantity_previous: Decimal | None = None
    price_current: Decimal | None = None
    price_previous: Decimal | None = None
    volume_effect: Decimal | None = None
    price_effect: Decimal | None = None


@dataclass(frozen=True)
class Comparison:
    currency: str
    current: Decimal
    previous: Decimal
    change: Decimal
    change_percent: Decimal | None
    rows: list[ChangeRow] | None


@dataclass(frozen=True)
class TrendMonth:
    year: int
    month: int
    net_amount: Decimal


@dataclass(frozen=True)
class MonthFigure:
    currency: str
    net_amount: Decimal
    order_count: int | None
    previous_change_percent: Decimal | None
    complete: bool
    trend: list[TrendMonth]
