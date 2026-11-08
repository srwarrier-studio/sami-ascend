from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable

from butterfly.application.alpha import external
from butterfly.application.usecase.create_sales_order import utc_now
from butterfly.domain.entities.purchase_order import PurchaseOrder, PurchaseOrderItem
from butterfly.domain.entities.purchase_requisition import NOT_PROCESSED
from butterfly.domain.errors import ETagMismatch, ETagRequired, ValidationDetail, ValidationFailed
from butterfly.domain.repositories.purchase_order_repo import PurchaseOrderRepo
from butterfly.domain.repositories.purchase_requisition_repo import PurchaseRequisitionRepo

DELETION_CODE = "L"


class PurchaseOrderNotFound(Exception): ...


class DeletePurchaseOrderItem:
    def __init__(self, orders: PurchaseOrderRepo, requisitions: PurchaseRequisitionRepo, now: Callable[[], datetime] = utc_now):
        self.orders = orders
        self.requisitions = requisitions
        self.now = now

    def execute(self, purchase_order: str, item_number: str, if_match: str | None, body: dict[str, Any]) -> PurchaseOrder:
        order = self.orders.get(purchase_order)
        item = None if order is None else next((i for i in order.items if external(i.purchase_order_item) == external(item_number)), None)
        if item is None:
            raise PurchaseOrderNotFound(f"{purchase_order}/{item_number}")
        if if_match is None:
            raise ETagRequired()
        if if_match != order.etag:
            raise ETagMismatch()
        self.check(body, item)
        moment = self.now().astimezone(timezone.utc).replace(microsecond=0)
        last = order.last_change_date_time
        last = last.astimezone(timezone.utc) if last.tzinfo else last.replace(tzinfo=timezone.utc)
        changed_at = max(moment, last + timedelta(seconds=1))
        self.orders.cancel_item(purchase_order, item.purchase_order_item, changed_at)
        self.reopen(item, changed_at)
        return self.orders.get(purchase_order)

    def check(self, body: dict, item: PurchaseOrderItem) -> None:
        problems = []
        if body != {"PurchasingDocumentDeletionCode": DELETION_CODE}:
            problems.append(ValidationDetail("CHANGE_NOT_SUPPORTED", f"Only PurchasingDocumentDeletionCode {DELETION_CODE} can be set.", "PurchasingDocumentDeletionCode"))
        elif item.is_cancelled:
            problems.append(ValidationDetail("ITEM_ALREADY_DELETED", "The item is already deleted.", "PurchasingDocumentDeletionCode"))
        elif item.delivery.delivered_quantity > 0:
            problems.append(ValidationDetail("ITEM_RECEIVED", "Goods were already received for the item, it cannot be deleted.", "PurchasingDocumentDeletionCode"))
        if problems:
            raise ValidationFailed(problems)

    def reopen(self, item: PurchaseOrderItem, changed_at: datetime) -> None:
        if not item.purchase_requisition:
            return
        requisition = self.requisitions.get(item.purchase_requisition)
        if requisition is None:
            return
        items = []
        for r in requisition.items:
            if r.purchase_requisition_item == item.purchase_requisition_item:
                left = max(r.ordered_quantity - item.delivery.ordered_quantity, Decimal("0.000"))
                r = replace(r, ordered_quantity=left, **({} if left else {"processing_status": NOT_PROCESSED, "purchasing_document": "", "purchasing_document_item": ""}))
            items.append(r)
        self.requisitions.update(replace(requisition, items=items, last_change_date_time=max(changed_at, requisition.last_change_date_time + timedelta(seconds=1))))
