from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable

from butterfly.application.usecase.create_purchase_requisition import decimal_of
from butterfly.application.usecase.create_sales_order import utc_now
from butterfly.domain.entities.master_data import ISO_UNITS
from butterfly.domain.entities.purchase_requisition import NOT_RELEASED, PurchaseRequisition, PurchaseRequisitionItem
from butterfly.domain.errors import ETagMismatch, ETagRequired, ValidationDetail, ValidationFailed
from butterfly.domain.repositories.purchase_requisition_repo import PurchaseRequisitionRepo

CHANGEABLE = {"RequestedQuantity", "BaseUnitISOCode"}


class RequisitionNotFound(Exception):
    def __init__(self, purchase_requisition: str):
        super().__init__(purchase_requisition)


def locked(item: PurchaseRequisitionItem) -> str | None:
    if item.is_deleted:
        return "is deleted"
    if item.processing_status != "N" or item.ordered_quantity > 0:
        return "is already ordered"
    if item.release_status != NOT_RELEASED:
        return "is released or in release"
    return None


class ItemEdit:
    def __init__(self, repo: PurchaseRequisitionRepo, now: Callable[[], datetime] = utc_now):
        self.repo = repo
        self.now = now

    def load(self, number: str, item_number: str, if_match: str | None) -> tuple[PurchaseRequisition, PurchaseRequisitionItem]:
        requisition = self.repo.get(number)
        if requisition is None:
            raise RequisitionNotFound(number)
        item = next((i for i in requisition.items if i.purchase_requisition_item == item_number), None)
        if item is None:
            raise RequisitionNotFound(f"{number}/{item_number}")
        if if_match is None:
            raise ETagRequired()
        if if_match != requisition.etag:
            raise ETagMismatch()
        reason = locked(item)
        if reason:
            raise ValidationFailed([ValidationDetail("ITEM_NOT_CHANGEABLE", f"Item {item_number} of requisition {number} {reason} and cannot be changed.", "PurchaseRequisitionItem")])
        return requisition, item

    def save(self, requisition: PurchaseRequisition, changed: PurchaseRequisitionItem) -> PurchaseRequisition:
        moment = self.now().astimezone(timezone.utc).replace(microsecond=0)
        items = [changed if i.purchase_requisition_item == changed.purchase_requisition_item else i for i in requisition.items]
        saved = replace(requisition, items=items, last_change_date_time=max(moment, requisition.last_change_date_time + timedelta(seconds=1)))
        self.repo.update(saved)
        return saved


class ChangePurchaseRequisitionItem(ItemEdit):
    def execute(self, number: str, item_number: str, if_match: str | None, body: dict[str, Any]) -> PurchaseRequisition:
        requisition, item = self.load(number, item_number, if_match)
        details = [ValidationDetail("FIELD_NOT_ALLOWED", f"{name} cannot be changed.", name) for name in body if name not in CHANGEABLE]
        if "RequestedQuantity" in body and "BaseUnitISOCode" not in body:
            details.append(ValidationDetail("FIELD_REQUIRED", "BaseUnitISOCode is required together with RequestedQuantity.", "BaseUnitISOCode"))
        if "BaseUnitISOCode" in body and "RequestedQuantity" not in body:
            details.append(ValidationDetail("FIELD_REQUIRED", "RequestedQuantity is required together with BaseUnitISOCode.", "RequestedQuantity"))
        quantity = decimal_of(body.get("RequestedQuantity"))
        if "RequestedQuantity" in body and (quantity is None or quantity <= 0 or quantity != quantity.quantize(Decimal("0.001"))):
            details.append(ValidationDetail("QUANTITY_NOT_POSITIVE", "RequestedQuantity must be a number above 0 with up to 3 decimals.", "RequestedQuantity"))
        if "BaseUnitISOCode" in body and body["BaseUnitISOCode"] != ISO_UNITS.get(item.base_unit, item.base_unit):
            details.append(ValidationDetail("UNIT_INVALID", f"The unit is not the unit of item {item_number}.", "BaseUnitISOCode"))
        if not body:
            details.append(ValidationDetail("NOTHING_TO_CHANGE", "Send RequestedQuantity and BaseUnitISOCode.", "body"))
        if details:
            raise ValidationFailed(details)
        return self.save(requisition, replace(item, requested_quantity=quantity.quantize(Decimal("0.001"))))


class DeletePurchaseRequisitionItem(ItemEdit):
    def execute(self, number: str, item_number: str, if_match: str | None) -> PurchaseRequisition:
        requisition, item = self.load(number, item_number, if_match)
        return self.save(requisition, replace(item, is_deleted=True))
