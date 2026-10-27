from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class DailySales:
    date: date
    net_amount: Decimal
    order_count: int
    currency: str


@dataclass(frozen=True)
class CustomerSales:
    customer: str
    name: str
    date: date
    net_amount: Decimal
    order_count: int
    currency: str


@dataclass(frozen=True)
class MaterialSales:
    material: str
    description: str
    date: date
    quantity: Decimal
    unit: str
    net_amount: Decimal
    currency: str


@dataclass(frozen=True)
class HighValueOrder:
    order: str
    customer_name: str
    order_date: date
    net_amount: Decimal
    currency: str
    status: str
