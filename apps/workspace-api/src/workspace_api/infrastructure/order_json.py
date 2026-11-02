from datetime import date
from decimal import Decimal

from workspace_api.domain.entities.sales_order import NewSalesOrder, NewSalesOrderItem


def order_to_dict(order: NewSalesOrder) -> dict:
    return {
        "sales_order_type": order.sales_order_type,
        "sold_to_party": order.sold_to_party,
        "transaction_currency": order.transaction_currency,
        "company_code": order.company_code,
        "requested_delivery_date": order.requested_delivery_date.isoformat() if order.requested_delivery_date else None,
        "items": [{"material": i.material, "quantity": str(i.quantity), "quantity_unit": i.quantity_unit} for i in order.items],
    }


def order_from_dict(body: dict) -> NewSalesOrder:
    delivery = body["requested_delivery_date"]
    return NewSalesOrder(
        body["sales_order_type"],
        body["sold_to_party"],
        body["transaction_currency"],
        date.fromisoformat(delivery) if delivery else None,
        [NewSalesOrderItem(i["material"], Decimal(i["quantity"]), i["quantity_unit"]) for i in body["items"]],
        body["company_code"],
    )
