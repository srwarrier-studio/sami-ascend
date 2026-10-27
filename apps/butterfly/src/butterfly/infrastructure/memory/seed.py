from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from butterfly.domain.entities.sales_order import SalesOrder, SalesOrderItem

CUSTOMERS = [
    ("0000100001", "Acme Industries"),
    ("0000100002", "Bharat Steels"),
    ("0000100003", "Cauvery Engineering"),
    ("0000100004", "Deccan Fabricators"),
    ("0000100005", "Eastern Castings"),
]

MATERIALS = [
    ("RM-1001", "Steel rod 12mm", "KG", Decimal("1250.00")),
    ("RM-1002", "Steel plate 5mm", "KG", Decimal("2500.00")),
    ("RM-1003", "Copper wire 2mm", "KG", Decimal("840.00")),
    ("RM-1004", "Aluminium sheet 3mm", "KG", Decimal("610.50")),
    ("RM-1005", "Bearing 6204", "EA", Decimal("95.00")),
    ("RM-1006", "Hex bolt M10", "EA", Decimal("4.25")),
]

USERS = ["SMANI", "KRAJAN", "PDEVI"]
STATUSES = ["A", "B", "C", "C", "A", "X", "B", "C"]
ORDER_COUNT = 30
DAYS = 10
FIRST_NUMBER = 12001


def build_seed(today: date) -> list[SalesOrder]:
    return [build_order(index, today) for index in range(ORDER_COUNT)]


def build_order(index: int, today: date) -> SalesOrder:
    number = f"{FIRST_NUMBER + index:010d}"
    order_date = today - timedelta(days=(ORDER_COUNT - 1 - index) * DAYS // ORDER_COUNT)
    customer_id, customer_name = CUSTOMERS[index % len(CUSTOMERS)]
    created = datetime.combine(order_date, time(9, 0), timezone.utc) + timedelta(minutes=index)
    items = [build_item(number, index, position) for position in range(2 + index % 2)]
    return SalesOrder(
        sales_order=number,
        sales_order_type="OR",
        sold_to_party=customer_id,
        customer_name=customer_name,
        order_date=order_date,
        requested_delivery_date=None if index % 7 == 0 else order_date + timedelta(days=7),
        transaction_currency="INR",
        total_net_amount=sum((item.net_amount for item in items), Decimal("0.00")),
        overall_status=STATUSES[index % len(STATUSES)],
        created_by_user=USERS[index % len(USERS)],
        creation_date_time=created,
        last_change_date_time=created,
        items=items,
    )


def build_item(number: str, index: int, position: int) -> SalesOrderItem:
    material, description, unit, price = MATERIALS[(index + position) % len(MATERIALS)]
    quantity = Decimal(10 * (1 + (index + position) % 5)).quantize(Decimal("0.001"))
    return SalesOrderItem(
        sales_order=number,
        sales_order_item=f"{(position + 1) * 10:06d}",
        material=material,
        material_description=description,
        quantity=quantity,
        quantity_unit=unit,
        net_amount=(quantity * price).quantize(Decimal("0.01")),
    )
