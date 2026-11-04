from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class NewPurchaseRequisitionItem:
    material: str
    plant: str
    quantity: Decimal
    unit: str
    delivery_date: date
    text: str | None = None


@dataclass(frozen=True)
class NewPurchaseRequisition:
    description: str
    items: list[NewPurchaseRequisitionItem]


@dataclass(frozen=True)
class PurchaseRequisitionItem:
    item: str
    material: str
    text: str
    plant: str
    company_code: str
    quantity: Decimal
    unit: str
    net_amount: Decimal
    currency: str
    delivery_date: date
    release_status: str
    release_status_code: str
    ordered: bool
    deleted: bool
    purchase_order: str


@dataclass(frozen=True)
class PurchaseRequisition:
    purchase_requisition: str
    description: str
    created_by_user: str
    created_on: date | None
    last_change: datetime | None
    items: list[PurchaseRequisitionItem] = field(default_factory=list)

    @property
    def company_codes(self) -> set[str]:
        return {item.company_code for item in self.items}

    @property
    def total_net_amount(self) -> Decimal:
        return sum((item.net_amount for item in self.items if not item.deleted), Decimal("0.00"))


@dataclass(frozen=True)
class PurchaseRequisitionPage:
    requisitions: list[PurchaseRequisition]
    total: int
