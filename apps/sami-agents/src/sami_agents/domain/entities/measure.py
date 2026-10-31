from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DimensionInfo:
    name: str
    splits_volume_and_price: bool


@dataclass(frozen=True)
class MetricInfo:
    name: str
    label: str
    dimensions: tuple[DimensionInfo, ...]


@dataclass(frozen=True)
class MoverRow:
    key: str
    name: str
    current: Decimal
    previous: Decimal
    change: Decimal
    share_percent: Decimal | None
    unit: str | None = None
    volume_effect: Decimal | None = None
    price_effect: Decimal | None = None


@dataclass(frozen=True)
class Comparison:
    currency: str
    current: Decimal
    previous: Decimal
    change: Decimal
    change_percent: Decimal | None
    rows: list[MoverRow] | None = None


@dataclass(frozen=True)
class TrendPoint:
    month: str
    amount: Decimal
