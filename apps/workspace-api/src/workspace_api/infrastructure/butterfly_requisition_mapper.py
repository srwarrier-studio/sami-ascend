from datetime import date, datetime
from decimal import Decimal

from workspace_api.domain.entities.purchase_requisition import (
    NewPurchaseRequisition,
    PurchaseRequisition,
    PurchaseRequisitionItem,
)

RELEASE_WORDS = {"01": "not_released", "02": "in_release", "03": "released"}
ITEM_FIELDS = {
    "Material": "material",
    "Plant": "plant",
    "RequestedQuantity": "quantity",
    "BaseUnit": "unit",
    "BaseUnitISOCode": "unit",
    "DeliveryDate": "delivery_date",
    "PurchaseRequisitionItemText": "text",
}
ITEM_TARGET = "_PurchaseRequisitionItem/"


def new_requisition_to_json(requisition: NewPurchaseRequisition) -> dict:
    items = []
    for item in requisition.items:
        row = {
            "Material": item.material,
            "Plant": item.plant,
            "RequestedQuantity": str(item.quantity),
            "BaseUnit": item.unit,
            "DeliveryDate": item.delivery_date.isoformat(),
        }
        if item.text:
            row["PurchaseRequisitionItemText"] = item.text
        items.append(row)
    return {"PurReqnDescription": requisition.description, "_PurchaseRequisitionItem": items}


def target_from_json(target: str) -> str:
    if target.startswith(ITEM_TARGET):
        position, _, name = target[len(ITEM_TARGET) :].partition("/")
        return f"items/{position}/{ITEM_FIELDS.get(name, name)}"
    return {"PurReqnDescription": "description", "_PurchaseRequisitionItem": "items"}.get(target, target)


def item_from_json(data: dict) -> PurchaseRequisitionItem:
    return PurchaseRequisitionItem(
        item=data["PurchaseRequisitionItem"],
        material=data["Material"],
        text=data["PurchaseRequisitionItemText"],
        plant=data["Plant"],
        company_code=data["CompanyCode"],
        quantity=Decimal(str(data["RequestedQuantity"])),
        unit=data["BaseUnit"],
        net_amount=Decimal(str(data["ItemNetAmount"])),
        currency=data["PurReqnItemCurrency"],
        delivery_date=date.fromisoformat(data["DeliveryDate"]),
        release_status=RELEASE_WORDS.get(data["PurReqnReleaseStatus"], data["PurReqnReleaseStatus"]),
        release_status_code=data["PurReqnReleaseStatus"],
        ordered=data["ProcessingStatus"] == "B",
        deleted=data["IsDeleted"],
        purchase_order=data["PurchasingDocument"],
    )


def requisition_from_json(data: dict) -> PurchaseRequisition:
    items = [item_from_json(row) for row in data.get("_PurchaseRequisitionItem", [])]
    created = next((row["PurReqCreationDate"] for row in data.get("_PurchaseRequisitionItem", []) if row["PurReqCreationDate"]), None)
    return PurchaseRequisition(
        purchase_requisition=data["PurchaseRequisition"],
        description=data["PurReqnDescription"],
        created_by_user=next((row["CreatedByUser"] for row in data.get("_PurchaseRequisitionItem", [])), ""),
        created_on=date.fromisoformat(created) if created else None,
        last_change=None,
        items=items,
    )
