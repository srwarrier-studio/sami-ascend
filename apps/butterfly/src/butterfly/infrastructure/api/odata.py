from datetime import datetime, timezone

from butterfly.domain.entities.sales_order import SalesOrder

ROOT = "/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/"


def timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def order_to_json(order: SalesOrder) -> dict:
    return {
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


def etag(order: SalesOrder) -> str:
    return 'W/"' + order.last_change_date_time.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S") + '"'


def error_body(code: str, message: str, target: str | None = None) -> dict:
    error = {"code": code, "message": message}
    if target is not None:
        error["target"] = target
    return {"error": error}
