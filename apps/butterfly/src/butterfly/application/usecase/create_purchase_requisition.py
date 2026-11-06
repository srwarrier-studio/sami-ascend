import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Callable

from butterfly.application.alpha import internal
from butterfly.application.usecase.create_sales_order import utc_now
from butterfly.domain.entities.master_data import (
    DEFAULT_PURCHASING_GROUP,
    ISO_UNITS,
    PLANT_COMPANIES,
    PURCHASING_ORGANIZATIONS,
)
from butterfly.domain.entities.purchase_requisition import PurchaseRequisition, PurchaseRequisitionItem
from butterfly.domain.errors import ValidationDetail, ValidationFailed
from butterfly.domain.entities.release_rule import RELEASE_RULES, ReleaseRule, with_release_status
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.domain.repositories.purchase_requisition_repo import PurchaseRequisitionRepo

CREATED_BY = "BUTTERFLY"
DEFAULT_CURRENCY = "INR"
REQUISITION_TYPES = {"NB"}
HEADER_FIELDS = {"PurchaseRequisitionType", "PurReqnDescription", "_PurchaseRequisitionItem"}
ITEM_FIELDS = {
    "Material", "Plant", "RequestedQuantity", "BaseUnit", "BaseUnitISOCode", "DeliveryDate", "PurchaseRequisitionItemText",
    "MaterialGroup", "PurchasingGroup", "PurReqnItemCurrency", "PurchaseRequisitionPrice", "Supplier",
}
DATE_FORMAT = re.compile(r"\d{4}-\d{2}-\d{2}")


def decimal_of(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


@dataclass
class Checker:
    master_data: MasterDataRepo
    today: date

    def __post_init__(self):
        self.details: list[ValidationDetail] = []

    def problem(self, code: str, message: str, target: str):
        self.details.append(ValidationDetail(code, message, target))

    def unknown_fields(self, body: dict, allowed: set[str], prefix: str):
        for name in body:
            if name not in allowed:
                self.problem("FIELD_NOT_ALLOWED", f"{name} is not a field that can be sent.", prefix + name)

    def delivery_date(self, entry: dict, prefix: str) -> date | None:
        value = entry.get("DeliveryDate")
        if value is None:
            self.problem("FIELD_REQUIRED", "DeliveryDate is required.", prefix + "DeliveryDate")
            return None
        try:
            if not isinstance(value, str) or not DATE_FORMAT.fullmatch(value):
                raise ValueError
            parsed = date.fromisoformat(value)
        except ValueError:
            self.problem("FIELD_INVALID", "DeliveryDate must be a date like 2026-11-05.", prefix + "DeliveryDate")
            return None
        if parsed < self.today:
            self.problem("DELIVERY_DATE_IN_PAST", "DeliveryDate must not be before today.", prefix + "DeliveryDate")
            return None
        return parsed

    def quantity(self, entry: dict, prefix: str) -> Decimal | None:
        if "RequestedQuantity" not in entry:
            self.problem("FIELD_REQUIRED", "RequestedQuantity is required.", prefix + "RequestedQuantity")
            return None
        quantity = decimal_of(entry["RequestedQuantity"])
        if quantity is None or quantity != quantity.quantize(Decimal("0.001")):
            self.problem("FIELD_INVALID", "RequestedQuantity must be a number with up to 3 decimals.", prefix + "RequestedQuantity")
            return None
        if quantity <= 0:
            self.problem("QUANTITY_NOT_POSITIVE", "RequestedQuantity must be greater than 0.", prefix + "RequestedQuantity")
            return None
        return quantity.quantize(Decimal("0.001"))


class CreatePurchaseRequisition:
    def __init__(self, repo: PurchaseRequisitionRepo, master_data: MasterDataRepo, now: Callable[[], datetime] = utc_now, rules: tuple[ReleaseRule, ...] = RELEASE_RULES):
        self.repo = repo
        self.master_data = master_data
        self.now = now
        self.rules = rules

    def execute(self, body: dict[str, Any]) -> PurchaseRequisition:
        moment = self.now().astimezone(timezone.utc).replace(microsecond=0)
        check = Checker(self.master_data, moment.date())
        number = self.repo.next_number()
        check.unknown_fields(body, HEADER_FIELDS, "")
        requisition_type = body.get("PurchaseRequisitionType", "NB")
        if requisition_type not in REQUISITION_TYPES:
            check.problem("FIELD_INVALID", f"PurchaseRequisitionType {requisition_type} is not valid.", "PurchaseRequisitionType")
        raw = body.get("_PurchaseRequisitionItem")
        if not isinstance(raw, list) or not raw:
            check.problem("NO_ITEMS", "A purchase requisition needs at least one item.", "_PurchaseRequisitionItem")
            raw = []
        items = [self.item(check, entry, number, position) for position, entry in enumerate(raw)]
        if check.details:
            raise ValidationFailed(check.details)
        items = [with_release_status(item, requisition_type, self.rules) for item in items]
        requisition = PurchaseRequisition(number, requisition_type, body.get("PurReqnDescription", ""), CREATED_BY, moment, moment, items)
        self.repo.add(requisition)
        return requisition

    def item(self, check: Checker, entry: Any, number: str, position: int) -> PurchaseRequisitionItem | None:
        prefix = f"_PurchaseRequisitionItem/{position}/"
        if not isinstance(entry, dict):
            check.problem("FIELD_INVALID", "Each item must be an object.", prefix.rstrip("/"))
            return None
        check.unknown_fields(entry, ITEM_FIELDS, prefix)
        plant = entry.get("Plant")
        company = PLANT_COMPANIES.get(plant)
        if plant is None:
            check.problem("FIELD_REQUIRED", "Plant is required.", prefix + "Plant")
        elif company is None:
            check.problem("PLANT_UNKNOWN", f"Plant {plant} does not exist.", prefix + "Plant")
        material = self.material(check, entry, company, prefix)
        quantity = check.quantity(entry, prefix)
        delivery = check.delivery_date(entry, prefix)
        unit = self.unit(check, entry, material, prefix)
        currency = entry.get("PurReqnItemCurrency", DEFAULT_CURRENCY)
        if not self.master_data.currency_exists(currency):
            check.problem("CURRENCY_INVALID", f"Currency {currency} is not valid.", prefix + "PurReqnItemCurrency")
        if None in (company, material, quantity, delivery, unit) or check.details:
            return None
        price = decimal_of(entry.get("PurchaseRequisitionPrice"))
        return PurchaseRequisitionItem(
            number, f"{(position + 1) * 10}", material.material_id, entry.get("PurchaseRequisitionItemText") or material.description,
            entry.get("MaterialGroup", ""), quantity, unit,
            (price if price is not None else material.price_in(currency)).quantize(Decimal("0.01"), ROUND_HALF_UP), currency, plant, company,
            PURCHASING_ORGANIZATIONS[company], entry.get("PurchasingGroup", DEFAULT_PURCHASING_GROUP), delivery, supplier=internal(entry.get("Supplier", "")),
        )

    def material(self, check: Checker, entry: dict, company: str | None, prefix: str):
        material_id = entry.get("Material")
        if material_id is None:
            check.problem("FIELD_REQUIRED", "Material is required.", prefix + "Material")
            return None
        material = self.master_data.get_material(material_id)
        if material is None or (company is not None and material.company_code != company):
            where = f" in plant {entry.get('Plant')}" if material is not None else ""
            check.problem("MATERIAL_UNKNOWN", f"Material {material_id} does not exist{where}.", prefix + "Material")
            return None
        return material

    def unit(self, check: Checker, entry: dict, material, prefix: str) -> str | None:
        sap_unit, iso_unit = entry.get("BaseUnit"), entry.get("BaseUnitISOCode")
        if sap_unit is None and iso_unit is None:
            check.problem("FIELD_REQUIRED", "BaseUnit or BaseUnitISOCode is required.", prefix + "BaseUnit")
            return None
        if material is None:
            return None
        if sap_unit is not None and sap_unit != material.unit or iso_unit is not None and iso_unit != ISO_UNITS.get(material.unit, material.unit):
            check.problem("UNIT_INVALID", f"The unit is not valid for material {material.material_id}.", prefix + "BaseUnit")
            return None
        return material.unit
