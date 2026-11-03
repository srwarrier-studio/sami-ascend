from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class CashDay:
    day: date
    direction: str
    count: int
    amount: Decimal


@dataclass(frozen=True)
class ExpenseDay:
    day: date
    category: str
    count: int
    amount: Decimal


@dataclass(frozen=True)
class IncomingPayment:
    payment: str
    day: date
    customer: str
    amount: Decimal
