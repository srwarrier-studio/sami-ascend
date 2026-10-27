from datetime import date, datetime
from decimal import Decimal

from workspace_api.domain.entities.sales_order import NewSalesOrder, SalesOrder, SalesOrderItem


def new_order_to_json(order: NewSalesOrder) -> dict:
    body = {
        "SalesOrderType": order.sales_order_type,
        "SoldToParty": order.sold_to_party,
        "TransactionCurrency": order.transaction_currency,
        "_Item": [
            {"Material": i.material, "Quantity": str(i.quantity), "QuantityUnit": i.quantity_unit}
            for i in order.items
        ],
    }
    if order.requested_delivery_date:
        body["RequestedDeliveryDate"] = order.requested_delivery_date.isoformat()
    return body


def order_from_json(data: dict) -> SalesOrder:
    delivery = data["RequestedDeliveryDate"]
    return SalesOrder(
        sales_order=data["SalesOrder"],
        sales_order_type=data["SalesOrderType"],
        sold_to_party=data["SoldToParty"],
        customer_name=data["CustomerName"],
        order_date=date.fromisoformat(data["OrderDate"]),
        requested_delivery_date=date.fromisoformat(delivery) if delivery else None,
        transaction_currency=data["TransactionCurrency"],
        total_net_amount=Decimal(data["TotalNetAmount"]),
        overall_status=data["OverallStatus"],
        created_by_user=data["CreatedByUser"],
        creation_date_time=datetime.fromisoformat(data["CreationDateTime"]),
        last_change_date_time=datetime.fromisoformat(data["LastChangeDateTime"]),
        items=[item_from_json(i) for i in data.get("_Item", [])],
    )


def item_from_json(data: dict) -> SalesOrderItem:
    return SalesOrderItem(
        sales_order_item=data["SalesOrderItem"],
        material=data["Material"],
        material_description=data["MaterialDescription"],
        quantity=Decimal(data["Quantity"]),
        quantity_unit=data["QuantityUnit"],
        net_amount=Decimal(data["NetAmount"]),
    )
