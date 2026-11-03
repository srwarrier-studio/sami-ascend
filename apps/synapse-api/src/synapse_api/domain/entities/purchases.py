from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class DailyPurchases:
    date: date
    net_amount: Decimal
    order_count: int
    currency: str


@dataclass(frozen=True)
class SupplierPurchases:
    supplier: str
    name: str
    date: date
    net_amount: Decimal
    order_count: int
    currency: str


@dataclass(frozen=True)
class PurchaseItem:
    order: str
    item: str
    supplier_name: str
    order_date: date
    promised: date
    actual: date | None
    net_amount: Decimal
    currency: str
    status: str


@dataclass(frozen=True)
class GroupPurchases:
    group: str
    name: str
    date: date
    net_amount: Decimal
    order_count: int
    currency: str
