from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from butterfly.domain.entities.drivers import PurchaseDelivery

CANCELLED = "X"


@dataclass(frozen=True)
class PurchaseOrderItem:
    delivery: PurchaseDelivery
    plant: str = ""
    purchase_requisition: str = ""
    purchase_requisition_item: str = ""

    @property
    def purchase_order_item(self) -> str:
        return self.delivery.purchase_order_item

    @property
    def is_cancelled(self) -> bool:
        return self.delivery.delivery_status == CANCELLED

    def cancelled(self) -> "PurchaseOrderItem":
        return replace(self, delivery=replace(self.delivery, delivery_status=CANCELLED))


@dataclass(frozen=True)
class PurchaseOrder:
    purchase_order: str
    order_type: str
    company_code: str
    purchasing_organization: str
    purchasing_group: str
    supplier: str
    document_currency: str
    created_by_user: str
    creation_date_time: datetime
    last_change_date_time: datetime
    items: list[PurchaseOrderItem] = field(default_factory=list)

    @property
    def etag(self) -> str:
        moment = self.last_change_date_time
        moment = moment.astimezone(timezone.utc) if moment.tzinfo else moment
        return f'W/"{moment.strftime("%Y%m%d%H%M%S")}"'
