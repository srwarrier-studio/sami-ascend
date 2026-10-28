from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class SalesTotal:
    start: date
    end: date
    net_amount: Decimal
    order_count: int
    currency: str


@dataclass(frozen=True)
class RankedCustomer:
    customer: str
    name: str
    net_amount: Decimal
    order_count: int
    currency: str


@dataclass(frozen=True)
class RankedMaterial:
    material: str
    description: str
    quantity: Decimal
    unit: str
    net_amount: Decimal
    currency: str


@dataclass(frozen=True)
class MonthSales:
    year: int
    month: int
    net_amount: Decimal
    currency: str
