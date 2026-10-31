from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class SalesContract:
    sales_contract: str
    predecessor_contract: str | None
    sold_to_party: str
    customer_name: str | None
    valid_from: date
    valid_to: date
    contract_value: Decimal
    transaction_currency: str
    contract_status: str


@dataclass(frozen=True)
class PurchaseDelivery:
    purchase_order: str
    purchase_order_item: str
    supplier: str
    supplier_name: str | None
    material: str
    material_description: str | None
    order_date: date
    ordered_quantity: Decimal
    delivered_quantity: Decimal
    quantity_unit: str
    promised_delivery_date: date
    actual_delivery_date: date | None
    delivery_status: str


@dataclass(frozen=True)
class ProductionOrder:
    production_order: str
    material: str
    material_description: str | None
    planned_quantity: Decimal
    confirmed_quantity: Decimal
    quantity_unit: str
    planned_start_date: date
    planned_end_date: date
    actual_end_date: date | None
    production_status: str
    delay_reason: str | None


@dataclass(frozen=True)
class ProductionOrderComponent:
    production_order: str
    material: str
    material_description: str | None
    required_quantity: Decimal
    quantity_unit: str
