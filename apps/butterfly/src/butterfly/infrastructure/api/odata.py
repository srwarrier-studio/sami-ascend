from datetime import date, datetime, timezone
from decimal import Decimal

from butterfly.domain.entities.sales_order import SalesOrder, SalesOrderItem

ROOT = "/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/"


def timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def order_to_json(order: SalesOrder, fields: list[str] | None = None) -> dict:
    row = {
        "SalesOrder": order.sales_order,
        "SalesOrderType": order.sales_order_type,
        "SoldToParty": order.sold_to_party,
        "CustomerName": order.customer_name,
        "OrderDate": order.order_date.isoformat(),
        "RequestedDeliveryDate": (
            order.requested_delivery_date.isoformat() if order.requested_delivery_date else None
        ),
        "TransactionCurrency": order.transaction_currency,
        "TotalNetAmount": str(order.total_net_amount),
        "OverallStatus": order.overall_status,
        "CreatedByUser": order.created_by_user,
        "CreationDateTime": timestamp(order.creation_date_time),
        "LastChangeDateTime": timestamp(order.last_change_date_time),
    }
    if fields is None:
        return row
    return {name: row[name] for name in fields}


def item_to_json(item: SalesOrderItem, fields: list[str] | None = None) -> dict:
    row = {
        "SalesOrder": item.sales_order,
        "SalesOrderItem": item.sales_order_item,
        "Material": item.material,
        "MaterialDescription": item.material_description,
        "Quantity": str(item.quantity),
        "QuantityUnit": item.quantity_unit,
        "NetAmount": str(item.net_amount),
    }
    if fields is None:
        return row
    return {name: row[name] for name in fields}


def summary_to_json(row, fields: dict, select: list[str] | None = None) -> dict:
    values = {}
    for name, (attribute, _) in fields.items():
        value = getattr(row, attribute)
        if isinstance(value, Decimal):
            value = str(value)
        elif isinstance(value, date):
            value = value.isoformat()
        values[name] = value
    return values if select is None else {name: values[name] for name in select}


def error_body(
    code: str, message: str, target: str | None = None, details: list[dict] | None = None
) -> dict:
    error = {"code": code, "message": message}
    if target is not None:
        error["target"] = target
    if details is not None:
        error["details"] = details
    return {"error": error}
