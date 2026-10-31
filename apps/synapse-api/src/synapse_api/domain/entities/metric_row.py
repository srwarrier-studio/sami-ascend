from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class MetricRow:
    key: str | None
    name: str
    date: date
    amount: Decimal
    currency: str
    quantity: Decimal | None = None
    unit: str | None = None
    count: int | None = None
