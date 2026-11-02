from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class SalesSummaryByDay:
    order_date: date
    total_net_amount: Decimal
    order_count: int
    currency: str
    company_code: str = "INA1"


@dataclass(frozen=True)
class SalesSummaryByCustomer:
    sold_to_party: str
    customer_name: str | None
    order_date: date
    total_net_amount: Decimal
    order_count: int
    currency: str
    company_code: str = "INA1"


@dataclass(frozen=True)
class SalesSummaryByMaterial:
    material: str
    material_description: str | None
    order_date: date
    total_quantity: Decimal
    quantity_unit: str
    total_net_amount: Decimal
    currency: str
    company_code: str = "INA1"


@dataclass(frozen=True)
class PurchaseSummaryByDay:
    order_date: date
    total_net_amount: Decimal
    order_count: int
    currency: str
    company_code: str = "INA1"


@dataclass(frozen=True)
class PurchaseSummaryBySupplier:
    supplier: str
    supplier_name: str | None
    order_date: date
    total_net_amount: Decimal
    order_count: int
    currency: str
    company_code: str = "INA1"


@dataclass(frozen=True)
class PurchaseSummaryByMaterial:
    material: str
    material_description: str | None
    order_date: date
    total_quantity: Decimal
    quantity_unit: str
    total_net_amount: Decimal
    currency: str
    company_code: str = "INA1"


@dataclass(frozen=True)
class ReceivablesSummary:
    as_of_date: date
    open_amount: Decimal
    overdue_amount: Decimal
    open_count: int
    overdue_count: int
    currency: str
    company_code: str = "INA1"


@dataclass(frozen=True)
class ReceivablesByCustomer:
    sold_to_party: str
    customer_name: str | None
    as_of_date: date
    open_amount: Decimal
    overdue_amount: Decimal
    open_count: int
    overdue_count: int
    currency: str
    company_code: str = "INA1"


@dataclass(frozen=True)
class ReceivablesAgeing:
    as_of_date: date
    age_bucket: str
    open_amount: Decimal
    open_count: int
    currency: str
    company_code: str = "INA1"
