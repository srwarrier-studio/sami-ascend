from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from butterfly.domain.entities.master_data import LOCAL_CURRENCY, to_local


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
    company_code: str = "INA1"


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
    net_amount: Decimal = Decimal("0.00")
    transaction_currency: str = "INR"
    company_code: str = "INA1"

    @property
    def net_amount_local(self) -> Decimal:
        return to_local(self.net_amount, self.transaction_currency)

    @property
    def local_currency(self) -> str:
        return LOCAL_CURRENCY


@dataclass(frozen=True)
class CustomerInvoice:
    invoice: str
    sold_to_party: str
    customer_name: str | None
    invoice_date: date
    due_date: date
    net_amount: Decimal
    transaction_currency: str
    cleared_amount: Decimal
    clearing_date: date | None
    company_code: str = "INA1"
    country: str = "IN"

    @property
    def net_amount_local(self) -> Decimal:
        return to_local(self.net_amount, self.transaction_currency)

    @property
    def cleared_amount_local(self) -> Decimal:
        return to_local(self.cleared_amount, self.transaction_currency)


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
    company_code: str = "INA1"


@dataclass(frozen=True)
class ProductionOrderComponent:
    production_order: str
    material: str
    material_description: str | None
    required_quantity: Decimal
    quantity_unit: str
    company_code: str = "INA1"
