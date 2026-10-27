import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from butterfly.application.delivery_date import check_delivery_date
from butterfly.application.filter.fields import SALES_ORDER_FIELDS, SALES_ORDER_ITEM_FIELDS
from butterfly.domain.entities.master_data import Customer, Material
from butterfly.domain.errors import ValidationDetail
from butterfly.domain.repositories.master_data_repo import MasterDataRepo

HEADER_FIELDS = ["SalesOrderType", "SoldToParty", "RequestedDeliveryDate", "TransactionCurrency"]
ITEM_FIELDS = ["Material", "Quantity", "QuantityUnit"]
MAX_LENGTH = {
    "SalesOrderType": 4,
    "SoldToParty": 10,
    "TransactionCurrency": 5,
    "Material": 40,
    "QuantityUnit": 3,
}
QUANTITY_FORMAT = re.compile(r"-?\d{1,10}(?:\.\d{1,3})?")


@dataclass(frozen=True)
class NewItem:
    material: Material
    quantity: Decimal
    unit: str


@dataclass(frozen=True)
class NewOrder:
    sales_order_type: str
    customer: Customer
    requested_delivery_date: date | None
    currency: str
    items: list[NewItem]


class NewOrderValidator:
    def __init__(self, master_data: MasterDataRepo, today: date):
        self.master_data = master_data
        self.today = today
        self.details: list[ValidationDetail] = []

    def problem(self, code: str, message: str, target: str):
        self.details.append(ValidationDetail(code, message, target))

    def validate(self, body: dict[str, Any]) -> tuple[NewOrder | None, list[ValidationDetail]]:
        self.details = []
        self.check_not_allowed(body, HEADER_FIELDS + ["_Item"], "", SALES_ORDER_FIELDS)
        order_type = self.text(body, "SalesOrderType", "SalesOrderType")
        customer = self.customer(body)
        delivery_date = self.delivery_date(body)
        currency = self.currency(body)
        items = self.items(body)
        if self.details:
            return None, self.details
        return NewOrder(order_type, customer, delivery_date, currency, items), []

    def check_not_allowed(self, body: dict, allowed: list[str], prefix: str, known: dict):
        for name in body:
            if name in allowed:
                continue
            if name in known:
                message = f"{name} is set by SAP and cannot be sent."
            else:
                message = f"{name} is not a field of the sales order."
            self.problem("FIELD_NOT_ALLOWED", message, prefix + name)

    def text(self, body: dict, name: str, target: str) -> str | None:
        value = body.get(name)
        if value is None or (isinstance(value, str) and not value.strip()):
            self.problem("FIELD_REQUIRED", f"{name} is required.", target)
            return None
        if not isinstance(value, str) or len(value) > MAX_LENGTH[name]:
            self.problem(
                "FIELD_INVALID",
                f"{name} must be text of at most {MAX_LENGTH[name]} characters.",
                target,
            )
            return None
        return value

    def customer(self, body: dict) -> Customer | None:
        customer_id = self.text(body, "SoldToParty", "SoldToParty")
        if customer_id is None:
            return None
        customer = self.master_data.get_customer(customer_id)
        if customer is None:
            self.problem("CUSTOMER_UNKNOWN", f"Customer {customer_id} does not exist.", "SoldToParty")
        return customer

    def delivery_date(self, body: dict) -> date | None:
        value = body.get("RequestedDeliveryDate")
        if value is None:
            return None
        parsed, detail = check_delivery_date(value, self.today)
        if detail is not None:
            self.details.append(detail)
        return parsed

    def currency(self, body: dict) -> str | None:
        currency = self.text(body, "TransactionCurrency", "TransactionCurrency")
        if currency is not None and not self.master_data.currency_exists(currency):
            self.problem("CURRENCY_INVALID", f"Currency {currency} is not valid.", "TransactionCurrency")
        return currency

    def items(self, body: dict) -> list[NewItem]:
        raw = body.get("_Item")
        if raw is None or raw == []:
            self.problem("NO_ITEMS", "A sales order needs at least one item.", "_Item")
            return []
        if not isinstance(raw, list):
            self.problem("FIELD_INVALID", "_Item must be a list of items.", "_Item")
            return []
        items = [self.item(entry, position) for position, entry in enumerate(raw)]
        return [item for item in items if item is not None]

    def item(self, entry: Any, position: int) -> NewItem | None:
        prefix = f"_Item/{position}/"
        if not isinstance(entry, dict):
            self.problem("FIELD_INVALID", "Each item must be an object.", f"_Item/{position}")
            return None
        self.check_not_allowed(entry, ITEM_FIELDS, prefix, SALES_ORDER_ITEM_FIELDS)
        material = self.material(entry, prefix)
        quantity = self.quantity(entry, prefix)
        unit = self.text(entry, "QuantityUnit", prefix + "QuantityUnit")
        if material is not None and unit is not None and unit != material.unit:
            self.problem(
                "UNIT_INVALID",
                f"Unit {unit} is not valid for material {material.material_id}.",
                prefix + "QuantityUnit",
            )
            return None
        if material is None or quantity is None or unit is None:
            return None
        return NewItem(material, quantity, unit)

    def material(self, entry: dict, prefix: str) -> Material | None:
        material_id = self.text(entry, "Material", prefix + "Material")
        if material_id is None:
            return None
        material = self.master_data.get_material(material_id)
        if material is None:
            self.problem("MATERIAL_UNKNOWN", f"Material {material_id} does not exist.", prefix + "Material")
        return material

    def quantity(self, entry: dict, prefix: str) -> Decimal | None:
        value = entry.get("Quantity")
        target = prefix + "Quantity"
        if value is None or (isinstance(value, str) and not value.strip()):
            self.problem("FIELD_REQUIRED", "Quantity is required.", target)
            return None
        if not isinstance(value, str) or not QUANTITY_FORMAT.fullmatch(value):
            self.problem(
                "FIELD_INVALID",
                "Quantity must be a decimal string with up to 3 decimals, like 50.000.",
                target,
            )
            return None
        quantity = Decimal(value)
        if quantity <= 0:
            self.problem("QUANTITY_NOT_POSITIVE", "Quantity must be greater than 0.", target)
            return None
        return quantity.quantize(Decimal("0.001"))
