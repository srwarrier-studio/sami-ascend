from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class NewSalesOrderItem:
    material: str
    quantity: Decimal
    quantity_unit: str


@dataclass(frozen=True)
class NewSalesOrder:
    sales_order_type: str
    sold_to_party: str
    transaction_currency: str
    requested_delivery_date: date | None
    items: list[NewSalesOrderItem]


@dataclass(frozen=True)
class SalesOrderItem:
    sales_order_item: str
    material: str
    material_description: str | None
    quantity: Decimal
    quantity_unit: str
    net_amount: Decimal


@dataclass(frozen=True)
class SalesOrder:
    sales_order: str
    sales_order_type: str
    sold_to_party: str
    customer_name: str | None
    order_date: date
    requested_delivery_date: date | None
    transaction_currency: str
    total_net_amount: Decimal
    overall_status: str
    created_by_user: str
    creation_date_time: datetime
    last_change_date_time: datetime
    items: list[SalesOrderItem] = field(default_factory=list)


@dataclass(frozen=True)
class SalesOrderPage:
    orders: list[SalesOrder]
    total: int
