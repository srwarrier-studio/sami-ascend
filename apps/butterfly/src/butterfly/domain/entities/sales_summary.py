from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class SalesSummaryByDay:
    order_date: date
    total_net_amount: Decimal
    order_count: int
    currency: str


@dataclass(frozen=True)
class SalesSummaryByCustomer:
    sold_to_party: str
    customer_name: str | None
    order_date: date
    total_net_amount: Decimal
    order_count: int
    currency: str


@dataclass(frozen=True)
class SalesSummaryByMaterial:
    material: str
    material_description: str | None
    order_date: date
    total_quantity: Decimal
    quantity_unit: str
    total_net_amount: Decimal
    currency: str
