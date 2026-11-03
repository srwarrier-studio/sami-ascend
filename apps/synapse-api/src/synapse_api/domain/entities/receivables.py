from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ReceivablesTotal:
    currency: str
    open_amount: Decimal
    overdue_amount: Decimal
    open_count: int
    overdue_count: int


@dataclass(frozen=True)
class CustomerReceivable:
    customer: str
    name: str
    currency: str
    open_amount: Decimal
    overdue_amount: Decimal


@dataclass(frozen=True)
class AgeBucket:
    bucket: str
    currency: str
    open_amount: Decimal
    open_count: int
