from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

NOT_RELEASED = "01"
IN_RELEASE = "02"
RELEASED = "03"
NOT_PROCESSED = "N"
ORDERED = "B"


@dataclass(frozen=True)
class PurchaseRequisitionItem:
    purchase_requisition: str
    purchase_requisition_item: str
    material: str
    item_text: str
    material_group: str
    requested_quantity: Decimal
    base_unit: str
    price: Decimal
    currency: str
    plant: str
    company_code: str
    purchasing_organization: str
    purchasing_group: str
    delivery_date: date
    release_status: str = NOT_RELEASED
    processing_status: str = NOT_PROCESSED
    release_codes: tuple[str, ...] = ()
    ordered_quantity: Decimal = Decimal("0")
    purchasing_document: str = ""
    purchasing_document_item: str = ""
    supplier: str = ""
    is_deleted: bool = False

    @property
    def net_amount(self) -> Decimal:
        return (self.requested_quantity * self.price).quantize(Decimal("0.01"))

    @property
    def release_is_not_completed(self) -> bool:
        return self.release_status != RELEASED


@dataclass(frozen=True)
class PurchaseRequisition:
    purchase_requisition: str
    requisition_type: str
    description: str
    created_by_user: str
    creation_date_time: datetime
    last_change_date_time: datetime
    items: list[PurchaseRequisitionItem] = field(default_factory=list)

    @property
    def etag(self) -> str:
        stamp = self.last_change_date_time.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f'W/"{stamp}"'
