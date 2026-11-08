from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from butterfly.application.alpha import external
from butterfly.application.usecase.create_purchase_requisition import DATE_FORMAT, decimal_of
from butterfly.application.usecase.create_sales_order import utc_now
from butterfly.domain.entities.drivers import PurchaseDelivery
from butterfly.domain.entities.master_data import DEFAULT_PURCHASING_GROUP, PLANT_COMPANIES, PURCHASING_ORGANIZATIONS, Material, Supplier
from butterfly.domain.entities.purchase_order import PurchaseOrder, PurchaseOrderItem
from butterfly.domain.entities.purchase_requisition import ORDERED, RELEASED, PurchaseRequisition, PurchaseRequisitionItem
from butterfly.domain.errors import ValidationDetail, ValidationFailed
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.domain.repositories.purchase_order_repo import PurchaseOrderRepo
from butterfly.domain.repositories.purchase_requisition_repo import PurchaseRequisitionRepo

CREATED_BY = "BUTTERFLY"
ORDER_TYPES = {"NB"}
OPEN = "O"
HEADER_FIELDS = {"PurchaseOrderType", "CompanyCode", "PurchasingOrganization", "PurchasingGroup", "Supplier", "DocumentCurrency", "_PurchaseOrderItem"}
ITEM_FIELDS = {
    "PurchaseRequisition", "PurchaseRequisitionItem", "Material", "Plant", "OrderQuantity", "PurchaseOrderQuantityUnit", "NetPriceAmount",
    "PurchaseOrderItemText", "_PurchaseOrderScheduleLineTP",
}
LINE_FIELDS = {"ScheduleLineDeliveryDate"}


@dataclass(frozen=True)
class Source:
    requisition: PurchaseRequisition
    item: PurchaseRequisitionItem


class CreatePurchaseOrder:
    def __init__(self, orders: PurchaseOrderRepo, requisitions: PurchaseRequisitionRepo, master_data: MasterDataRepo, now: Callable[[], datetime] = utc_now):
        self.orders = orders
        self.requisitions = requisitions
        self.master_data = master_data
        self.now = now

    def execute(self, body: dict[str, Any]) -> PurchaseOrder:
        moment = self.now().astimezone(timezone.utc).replace(microsecond=0)
        self.details: list[ValidationDetail] = []
        self.requested: dict[tuple[str, str], Decimal] = {}
        self.unknown(body, HEADER_FIELDS, "")
        order_type = body.get("PurchaseOrderType", "NB")
        if order_type not in ORDER_TYPES:
            self.problem("FIELD_INVALID", f"PurchaseOrderType {order_type} is not valid.", "PurchaseOrderType")
        company = self.company(body)
        supplier = self.supplier(body, company)
        currency = self.currency(body)
        raw = body.get("_PurchaseOrderItem")
        if not isinstance(raw, list) or not raw:
            self.problem("NO_ITEMS", "A purchase order needs at least one item.", "_PurchaseOrderItem")
            raw = []
        number = self.orders.next_number()
        built = [self.item(entry, position, number, moment.date(), company, supplier, currency) for position, entry in enumerate(raw)]
        if self.details:
            raise ValidationFailed(self.details)
        items = [item for item, _ in built]
        order = PurchaseOrder(
            number, order_type, company, body.get("PurchasingOrganization") or PURCHASING_ORGANIZATIONS[company],
            body.get("PurchasingGroup") or DEFAULT_PURCHASING_GROUP, supplier.supplier_id, currency, CREATED_BY, moment, moment, items,
        )
        self.orders.add(order)
        self.mark_ordered(number, [(source, item) for item, source in built if source])
        return order

    def problem(self, code: str, message: str, target: str) -> None:
        self.details.append(ValidationDetail(code, message, target))

    def unknown(self, body: dict, allowed: set[str], prefix: str) -> None:
        for name in body:
            if name not in allowed:
                self.problem("FIELD_NOT_ALLOWED", f"{name} is not a field that can be sent.", prefix + name)

    def company(self, body: dict) -> str:
        company = body.get("CompanyCode")
        if company is None:
            self.problem("FIELD_REQUIRED", "CompanyCode is required.", "CompanyCode")
        elif not self.master_data.company_exists(company):
            self.problem("COMPANY_UNKNOWN", f"Company code {company} does not exist.", "CompanyCode")
        return company or ""

    def supplier(self, body: dict, company: str) -> Supplier | None:
        wanted = body.get("Supplier")
        if wanted is None:
            self.problem("FIELD_REQUIRED", "Supplier is required.", "Supplier")
            return None
        found = next((s for s in self.master_data.list_suppliers() if external(s.supplier_id) == external(str(wanted))), None)
        if found is None:
            self.problem("SUPPLIER_UNKNOWN", f"Supplier {wanted} does not exist.", "Supplier")
        elif company and found.company_code != company:
            self.problem("SUPPLIER_COMPANY", f"Supplier {wanted} is not maintained for company code {company}.", "Supplier")
            return None
        return found

    def currency(self, body: dict) -> str:
        currency = body.get("DocumentCurrency", "INR")
        if not self.master_data.currency_exists(currency):
            self.problem("CURRENCY_INVALID", f"Currency {currency} is not valid.", "DocumentCurrency")
        return currency

    def item(self, entry: Any, position: int, number: str, today: date, company: str, supplier: Supplier | None, currency: str):
        prefix = f"_PurchaseOrderItem/{position}/"
        if not isinstance(entry, dict):
            self.problem("FIELD_INVALID", "Each item must be an object.", prefix.rstrip("/"))
            return None, None
        self.unknown(entry, ITEM_FIELDS, prefix)
        source = self.source(entry, prefix, company, currency) if entry.get("PurchaseRequisition") is not None else None
        if source is None and entry.get("PurchaseRequisition") is not None:
            return None, None
        material, plant = self.goods(entry, prefix, company, source)
        quantity = self.quantity(entry, prefix, source)
        delivery = self.delivery(entry, prefix, source, today)
        price = self.price(entry, prefix, material, currency, source)
        if None in (material, plant, quantity, delivery, price, supplier) or self.details:
            return None, None
        net = (quantity * price).quantize(Decimal("0.01"), ROUND_HALF_UP)
        line = f"{(position + 1) * 10:05d}"
        stored = PurchaseDelivery(
            number, line, supplier.supplier_id, supplier.name, material.material_id, entry.get("PurchaseOrderItemText") or material.description, today,
            quantity, Decimal("0.000"), material.unit, delivery, None, OPEN, net, currency, company,
        )
        link = (source.requisition.purchase_requisition, source.item.purchase_requisition_item) if source else ("", "")
        return PurchaseOrderItem(stored, plant, *link), source

    def source(self, entry: dict, prefix: str, company: str, currency: str) -> Source | None:
        number, line = str(entry["PurchaseRequisition"]), entry.get("PurchaseRequisitionItem")
        target = prefix + "PurchaseRequisition"
        requisition = self.requisitions.get(number)
        item = None if requisition is None or line is None else next((i for i in requisition.items if external(i.purchase_requisition_item) == external(str(line))), None)
        if item is None:
            self.problem("REQUISITION_ITEM_UNKNOWN", f"Purchase requisition item {number}/{line} does not exist.", target)
        elif item.is_deleted:
            self.problem("REQUISITION_ITEM_DELETED", f"Purchase requisition item {number}/{line} is deleted.", target)
        elif item.release_status != RELEASED:
            self.problem("REQUISITION_ITEM_NOT_RELEASED", f"Purchase requisition item {number}/{line} is not released.", target)
        elif item.requested_quantity - item.ordered_quantity <= 0:
            self.problem("REQUISITION_ITEM_ORDERED", f"Purchase requisition item {number}/{line} is already ordered.", target)
        elif item.currency != currency:
            self.problem("CURRENCY_MISMATCH", f"Purchase requisition item {number}/{line} is in {item.currency}, the order is in {currency}.", target)
        elif item.company_code != company:
            self.problem("COMPANY_MISMATCH", f"Purchase requisition item {number}/{line} belongs to company code {item.company_code}.", target)
        else:
            return Source(requisition, item)
        return None

    def goods(self, entry: dict, prefix: str, company: str, source: Source | None):
        if source:
            for name, value in (("Material", source.item.material), ("Plant", source.item.plant)):
                if entry.get(name) not in (None, value):
                    self.problem("REQUISITION_MISMATCH", f"{name} differs from the purchase requisition item.", prefix + name)
            return self.master_data.get_material(source.item.material), source.item.plant
        if not company:
            return None, None
        material = self.direct_material(entry, prefix, company)
        plant = entry.get("Plant")
        if plant is None:
            self.problem("FIELD_REQUIRED", "Plant is required.", prefix + "Plant")
        elif PLANT_COMPANIES.get(plant) is None:
            self.problem("PLANT_UNKNOWN", f"Plant {plant} does not exist.", prefix + "Plant")
        elif PLANT_COMPANIES[plant] != company:
            self.problem("PLANT_COMPANY", f"Plant {plant} does not belong to company code {company}.", prefix + "Plant")
        return material, plant if PLANT_COMPANIES.get(plant) == company else None

    def direct_material(self, entry: dict, prefix: str, company: str) -> Material | None:
        material_id = entry.get("Material")
        if material_id is None:
            self.problem("FIELD_REQUIRED", "Material is required.", prefix + "Material")
            return None
        material = self.master_data.get_material(material_id)
        if material is None or material.company_code != company:
            self.problem("MATERIAL_UNKNOWN", f"Material {material_id} does not exist.", prefix + "Material")
            return None
        unit = entry.get("PurchaseOrderQuantityUnit")
        if unit is not None and unit != material.unit:
            self.problem("UNIT_INVALID", f"The unit is not valid for material {material_id}.", prefix + "PurchaseOrderQuantityUnit")
        return material

    def quantity(self, entry: dict, prefix: str, source: Source | None) -> Decimal | None:
        target = prefix + "OrderQuantity"
        raw = entry.get("OrderQuantity")
        if raw is None and source is None:
            self.problem("FIELD_REQUIRED", "OrderQuantity is required.", target)
            return None
        quantity = decimal_of(raw) if raw is not None else source.item.requested_quantity - source.item.ordered_quantity
        if quantity is None or quantity != quantity.quantize(Decimal("0.001")):
            self.problem("FIELD_INVALID", "OrderQuantity must be a number with up to 3 decimals.", target)
            return None
        if quantity <= 0:
            self.problem("QUANTITY_NOT_POSITIVE", "OrderQuantity must be greater than 0.", target)
            return None
        if source:
            key = (source.requisition.purchase_requisition, source.item.purchase_requisition_item)
            self.requested[key] = self.requested.get(key, Decimal(0)) + quantity
            if self.requested[key] > source.item.requested_quantity - source.item.ordered_quantity:
                self.problem("QUANTITY_ABOVE_OPEN", "OrderQuantity is more than the open quantity of the purchase requisition item.", target)
                return None
        return quantity.quantize(Decimal("0.001"))

    def delivery(self, entry: dict, prefix: str, source: Source | None, today: date) -> date | None:
        lines = entry.get("_PurchaseOrderScheduleLineTP")
        value = lines[0].get("ScheduleLineDeliveryDate") if isinstance(lines, list) and lines and isinstance(lines[0], dict) else None
        target = prefix + "_PurchaseOrderScheduleLineTP/0/ScheduleLineDeliveryDate"
        if value is None:
            if source:
                return source.item.delivery_date
            self.problem("FIELD_REQUIRED", "ScheduleLineDeliveryDate is required.", target)
            return None
        try:
            if not isinstance(value, str) or not DATE_FORMAT.fullmatch(value):
                raise ValueError
            parsed = date.fromisoformat(value)
        except ValueError:
            self.problem("FIELD_INVALID", "ScheduleLineDeliveryDate must be a date like 2026-11-05.", target)
            return None
        if parsed < today:
            self.problem("DELIVERY_DATE_IN_PAST", "ScheduleLineDeliveryDate must not be before today.", target)
            return None
        return parsed

    def price(self, entry: dict, prefix: str, material: Material | None, currency: str, source: Source | None) -> Decimal | None:
        raw = entry.get("NetPriceAmount")
        if raw is None:
            if source:
                return source.item.price
            return material.price_in(currency) if material else None
        price = decimal_of(raw)
        if price is None or price < 0:
            self.problem("FIELD_INVALID", "NetPriceAmount must be a number of 0 or more.", prefix + "NetPriceAmount")
            return None
        return price.quantize(Decimal("0.01"), ROUND_HALF_UP)

    def mark_ordered(self, number: str, pairs: list[tuple[Source, PurchaseOrderItem]]) -> None:
        changed: dict[str, PurchaseRequisition] = {}
        for source, ordered in pairs:
            requisition = changed.get(source.requisition.purchase_requisition) or self.requisitions.get(source.requisition.purchase_requisition)
            items = [
                replace(
                    i, processing_status=ORDERED, ordered_quantity=i.ordered_quantity + ordered.delivery.ordered_quantity,
                    purchasing_document=number, purchasing_document_item=external(ordered.purchase_order_item),
                ) if i.purchase_requisition_item == source.item.purchase_requisition_item else i
                for i in requisition.items
            ]
            changed[requisition.purchase_requisition] = replace(requisition, items=items, last_change_date_time=self.now().astimezone(timezone.utc).replace(microsecond=0))
        for requisition in changed.values():
            self.requisitions.update(requisition)
