import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from butterfly.application.filter.fields import (
    STANDARD_V2_ITEM_FIELDS,
    STANDARD_V2_ORDER_FIELDS,
    STANDARD_V4_ITEM_FIELDS,
    STANDARD_V4_ORDER_FIELDS,
)
from butterfly.domain.entities.master_data import ISO_UNITS
from butterfly.domain.entities.sales_order import SalesOrder, SalesOrderItem
from butterfly.infrastructure.api.standard.edmx import V2_METADATA, V4_METADATA, Metadata, load

V4_ROOT = "/sap/opu/odata4/sap/api_salesorder/srvd_a2x/sap/salesorder/0001"
V2_ROOT = "/sap/opu/odata/sap/API_SALES_ORDER_SRV"
V4_METADATA_ETAG = 'W/"20261018073436"'
V4_MEDIA = "application/json;odata.metadata=minimal;charset=utf-8"
V2_MEDIA = "application/json; charset=utf-8"


class Refusal(Exception):
    def __init__(self, kind: str, token: str = ""):
        self.kind = kind
        self.token = token


@dataclass(frozen=True)
class ItemRow:
    sales_order: str
    sales_order_item: str
    material: str
    material_description: str | None
    quantity: Decimal
    quantity_unit: str
    net_amount: Decimal
    transaction_currency: str
    etag: str
    requested_delivery_date: date | None
    changed: datetime


def item_rows(order: SalesOrder) -> list[ItemRow]:
    return [
        ItemRow(i.sales_order, i.sales_order_item, i.material, i.material_description, i.quantity, i.quantity_unit, i.net_amount, order.transaction_currency, order.etag, order.requested_delivery_date, order.last_change_date_time)
        for i in order.items
    ]


def plain(number: str) -> str:
    return str(int(number)) if number.isdigit() else number


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S.%f")


def short(token: str) -> str:
    return token if len(token) <= 3 else token[:3] + "..."


def milliseconds(value: date | datetime) -> int:
    moment = value if isinstance(value, datetime) else datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    return int(moment.timestamp() * 1000)


def datetimeoffset_etag(moment: datetime) -> str:
    utc = moment.astimezone(timezone.utc)
    stamp_text = f"{utc:%Y-%m-%dT%H:%M:%S}.{utc.microsecond:06d}0Z"
    return f"W/\"datetimeoffset'{stamp_text.replace(':', '%3A')}'\""


def money_text(value: Decimal) -> str:
    return format(value, "f")


class V4:
    name = "V4"
    root = V4_ROOT
    media = V4_MEDIA
    order_set = "SalesOrder"
    item_set = "SalesOrderItem"
    nav = "_Item"
    order_fields = STANDARD_V4_ORDER_FIELDS
    item_fields = STANDARD_V4_ITEM_FIELDS
    count_option = "$count"
    supports_apply = True

    def __init__(self):
        self.metadata: Metadata = load(V4_METADATA)
        self.order_type = self.metadata.types["SalesOrder_Type"]
        self.item_type = self.metadata.types["SalesOrderItem_Type"]

    def blank(self, edm: str):
        if edm == "Edm.String":
            return ""
        if edm == "Edm.Boolean":
            return False
        if edm == "Edm.Decimal":
            return 0
        if edm.startswith("Collection("):
            return []
        return None

    def order_values(self, order: SalesOrder) -> dict:
        created = order.creation_date_time.astimezone(timezone.utc)
        delivery = order.requested_delivery_date
        return {
            "SalesOrder": plain(order.sales_order),
            "SalesOrderType": order.sales_order_type,
            "SoldToParty": order.sold_to_party,
            "SalesOrganization": order.sales_organization,
            "DistributionChannel": order.distribution_channel,
            "OrganizationDivision": order.division,
            "CreatedByUser": order.created_by_user,
            "CreationDate": created.date().isoformat(),
            "CreationTime": created.strftime("%H:%M:%S"),
            "LastChangeDateTime": order.last_change_date_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "PurchaseOrderByCustomer": order.purchase_order_by_customer or "",
            "SalesOrderDate": order.order_date.isoformat(),
            "RequestedDeliveryDate": delivery.isoformat() if delivery else None,
            "PricingDate": order.order_date.isoformat(),
            "TotalNetAmount": float(order.total_net_amount),
            "TransactionCurrency": order.transaction_currency,
            "BillingCompanyCode": order.company_code,
            "OverallSDProcessStatus": order.overall_status,
        }

    def item_values(self, item: ItemRow) -> dict:
        return {
            "SalesOrder": plain(item.sales_order),
            "SalesOrderItem": plain(item.sales_order_item),
            "Product": item.material,
            "SalesOrderItemText": item.material_description or "",
            "RequestedQuantity": float(item.quantity),
            "RequestedQuantitySAPUnit": item.quantity_unit,
            "RequestedQuantityISOUnit": ISO_UNITS.get(item.quantity_unit, item.quantity_unit),
            "NetAmount": float(item.net_amount),
            "TransactionCurrency": item.transaction_currency,
            "RequestedDeliveryDate": item.requested_delivery_date.isoformat() if item.requested_delivery_date else None,
        }

    def entity(self, entity_type, values: dict, etag: str, select: list[str] | None, keys: tuple[str, ...]) -> dict:
        row = {name: self.blank(edm) for name, edm in entity_type.properties}
        row |= {name: value for name, value in values.items() if name in row}
        wanted = select if select is None else [name for name, _ in entity_type.properties if name in select or name in keys]
        return {"@odata.etag": etag} | (row if wanted is None else {name: row[name] for name in wanted})

    def order_row(self, order: SalesOrder, select, expand, base: str) -> dict:
        row = self.entity(self.order_type, self.order_values(order), order.etag, select, ("SalesOrder",))
        if expand is not None:
            row[self.nav] = [self.item_row(i, expand[0] if expand else None, base) for i in item_rows(order)]
        return row

    def item_row(self, item: ItemRow, select, base: str) -> dict:
        return self.entity(self.item_type, self.item_values(item), item.etag, select, ("SalesOrder", "SalesOrderItem"))

    def context(self, entity: str, select: list[str] | None, expand_select: list[str] | None, expanded: bool) -> str:
        parts = list(select or [])
        if expanded:
            parts.append(self.nav + (f"({','.join(expand_select)})" if expand_select else ""))
        return "$metadata#" + entity + (f"({','.join(parts)})" if parts else "")

    def list_body(self, context: str, rows: list, total: int | None) -> dict:
        body = {"@odata.context": context, "@odata.metadataEtag": V4_METADATA_ETAG}
        if total is not None:
            body["@odata.count"] = total
        return body | {"value": rows}

    def entity_body(self, context: str, row: dict) -> dict:
        return {"@odata.context": context + "/$entity", "@odata.metadataEtag": V4_METADATA_ETAG} | row

    def expand_options(self, text: str | None):
        if text is None:
            return None
        match = re.fullmatch(r"_Item(?:\(\$select=([^)]*)\))?", text.strip())
        if match is None:
            raise Refusal("property", text.strip())
        return [match.group(1).split(",")] if match.group(1) else []

    def refusal(self, error: Refusal) -> tuple[int, dict]:
        kinds = {
            "parse": (400, f"/IWCOR/CX_OD_EXPR_PARSER_ERROR/00505692409C1EE681AE63616A3CC086", f"Invalid token '{short(error.token)}' at position '1'", "Client_Error"),
            "property": (400, "/IWCOR/CX_OD_SELECT_ERROR/00505692409C1ED5A0F4681CA94457B5", f"Property '{short(error.token)}' not found", "Client_Error"),
            "currency": (400, "/IWBEP/CM_V4S_RUN/031", f"Filter contains unit/currency amount '{error.token}' without matching unit/currency", "Client_Error"),
            "apply": (501, "SADL_GW/007", "$apply option not supported", "Provider_Application_Error"),
            "option": (400, "/IWBEP/CM_V4S_RUN/001", f"Invalid system query option '{error.token}' specified", "Client_Error"),
            "missing": (404, "/IWBEP/CM_V4S_RUN/004", "Resource not found for the segment 'SalesOrder'", "Client_Error"),
        }
        status, code, message, category = kinds[error.kind]
        body = {"code": code, "message": message, "@SAP__common.ExceptionCategory": category}
        if error.kind == "property":
            body["details"] = [{"code": "/IWCOR/CX_OD_EXPAND_ERROR/00505692409C1ED680ACB4DB13157E97", "message": "Invalid select option", "@SAP__common.Severity": "error", "@SAP__common.numericSeverity": 4}]
        body["innererror"] = {
            "ErrorDetails": {
                "@SAP__common.Application": {"ComponentId": "SD-SLS-API", "ServiceRepository": "SRVD_A2X", "ServiceId": "API_SALESORDER", "ServiceVersion": "0001"},
                "@SAP__common.TransactionId": uuid.uuid4().hex.upper(),
                "@SAP__common.Timestamp": stamp(),
                "@SAP__common.ErrorResolution": {
                    "Analysis": 'Use ADT feed reader "SAP Gateway Error Log" or run transaction /IWFND/ERROR_LOG on SAP Gateway hub system and search for entries with the timestamp above for more details',
                    "Note": "See SAP Note 1797736 for error analysis (https://service.sap.com/sap/support/notes/1797736)",
                },
            }
        }
        return status, {"error": body}


class V2:
    name = "V2"
    root = V2_ROOT
    media = V2_MEDIA
    order_set = "A_SalesOrder"
    item_set = "A_SalesOrderItem"
    nav = "to_Item"
    order_fields = STANDARD_V2_ORDER_FIELDS
    item_fields = STANDARD_V2_ITEM_FIELDS
    count_option = "$inlinecount"
    supports_apply = False

    def __init__(self):
        self.metadata: Metadata = load(V2_METADATA)
        self.order_type = self.metadata.types["A_SalesOrderType"]
        self.item_type = self.metadata.types["A_SalesOrderItemType"]

    def blank(self, edm: str):
        if edm == "Edm.String":
            return ""
        if edm == "Edm.Boolean":
            return False
        if edm == "Edm.Decimal":
            return "0"
        return None

    def order_values(self, order: SalesOrder) -> dict:
        created = order.creation_date_time.astimezone(timezone.utc)
        changed = order.last_change_date_time.astimezone(timezone.utc)
        delivery = order.requested_delivery_date
        day = f"/Date({milliseconds(order.order_date)})/"
        return {
            "SalesOrder": plain(order.sales_order),
            "SalesOrderType": order.sales_order_type,
            "SalesOrderTypeInternalCode": order.sales_order_type,
            "SalesOrganization": order.sales_organization,
            "DistributionChannel": order.distribution_channel,
            "OrganizationDivision": order.division,
            "SoldToParty": order.sold_to_party,
            "CreationDate": f"/Date({milliseconds(created.date())})/",
            "CreatedByUser": order.created_by_user,
            "LastChangeDate": f"/Date({milliseconds(changed.date())})/",
            "LastChangeDateTime": f"/Date({milliseconds(changed)}+0000)/",
            "PurchaseOrderByCustomer": order.purchase_order_by_customer or "",
            "SalesOrderDate": day,
            "TotalNetAmount": money_text(order.total_net_amount),
            "TransactionCurrency": order.transaction_currency,
            "PricingDate": day,
            "RequestedDeliveryDate": f"/Date({milliseconds(delivery)})/" if delivery else None,
            "OverallSDProcessStatus": order.overall_status,
        }

    def item_values(self, item: ItemRow) -> dict:
        return {
            "SalesOrder": plain(item.sales_order),
            "SalesOrderItem": plain(item.sales_order_item),
            "Material": item.material,
            "SalesOrderItemText": item.material_description or "",
            "RequestedQuantity": money_text(item.quantity),
            "RequestedQuantityUnit": item.quantity_unit,
            "NetAmount": money_text(item.net_amount),
            "TransactionCurrency": item.transaction_currency,
        }

    def metadata_block(self, entity_set: str, type_name: str, key: str, etag: str, base: str) -> dict:
        uri = f"{base}{self.root}/{entity_set}({key})"
        return {"id": uri, "uri": uri, "type": f"API_SALES_ORDER_SRV.{type_name}", "etag": etag}

    def order_row(self, order: SalesOrder, select, expand, base: str) -> dict:
        row = {name: self.blank(edm) for name, edm in self.order_type.properties}
        row |= {name: value for name, value in self.order_values(order).items() if name in row}
        key = f"'{plain(order.sales_order)}'"
        meta = self.metadata_block(self.order_set, "A_SalesOrderType", key, datetimeoffset_etag(order.last_change_date_time), base)
        if select is not None:
            row = {name: row[name] for name, _ in self.order_type.properties if name in select}
            links = {}
        else:
            links = {nav: {"__deferred": {"uri": f"{meta['uri']}/{nav}"}} for nav in self.order_type.navigation}
        if expand is not None:
            links[self.nav] = {"results": [self.item_row(i, expand[0] if expand else None, base) for i in item_rows(order)]}
        return {"__metadata": meta} | row | links

    def item_row(self, item: ItemRow, select, base: str) -> dict:
        row = {name: self.blank(edm) for name, edm in self.item_type.properties}
        row |= {name: value for name, value in self.item_values(item).items() if name in row}
        key = f"SalesOrder='{plain(item.sales_order)}',SalesOrderItem='{plain(item.sales_order_item)}'"
        meta = self.metadata_block(self.item_set, "A_SalesOrderItemType", key, datetimeoffset_etag(item.changed), base)
        if select is not None:
            return {"__metadata": meta} | {name: row[name] for name, _ in self.item_type.properties if name in select}
        links = {nav: {"__deferred": {"uri": f"{meta['uri']}/{nav}"}} for nav in self.item_type.navigation}
        return {"__metadata": meta} | row | links

    def context(self, entity: str, select, expand_select, expanded: bool) -> str:
        return ""

    def list_body(self, context: str, rows: list, total: int | None) -> dict:
        body = {"results": rows}
        if total is not None:
            body["__count"] = str(total)
        return {"d": body}

    def entity_body(self, context: str, row: dict) -> dict:
        return {"d": row}

    def expand_options(self, text: str | None):
        if text is None:
            return None
        if text.strip() != "to_Item":
            raise Refusal("property", text.strip())
        return []

    def refusal(self, error: Refusal) -> tuple[int, dict]:
        kinds = {
            "parse": (400, "005056A509B11EE1B9A8FEA8DE87F78E", f"Property {error.token} not found in type A_SalesOrderType"),
            "property": (400, "005056A509B11EE1B9A8FEA8DE87F78E", f"Property {error.token} not found in type A_SalesOrderType"),
            "currency": (400, "005056A509B11EE1B9A8FEA8DE87F78E", "Invalid filter expression"),
            "apply": (400, "00505692409C1ED98BC626766B3596A5", "Invalid system query option specified"),
            "option": (400, "00505692409C1ED98BC626766B3596A5", "Invalid system query option specified"),
            "missing": (404, "005056A509B11EE1B9A8FEA8DE87F78E", "Resource not found for segment 'A_SalesOrder'"),
        }
        status, code, message = kinds[error.kind]
        return status, {
            "error": {
                "code": code,
                "message": {"lang": "en", "value": message},
                "innererror": {
                    "transactionid": uuid.uuid4().hex.upper(),
                    "timestamp": stamp() + "0",
                    "Error_Resolution": {
                        "SAP_Transaction": 'For backend administrators: use ADT feed reader "SAP Gateway Error Log" or run transaction /IWFND/ERROR_LOG on SAP Gateway hub system and search for entries with the timestamp above for more details',
                        "SAP_Note": "See SAP Note 1797736 for error analysis (https://service.sap.com/sap/support/notes/1797736)",
                    },
                },
            }
        }
