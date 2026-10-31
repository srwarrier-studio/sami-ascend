from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from butterfly.domain.entities.drivers import (
    ProductionOrder,
    ProductionOrderComponent,
    PurchaseDelivery,
    SalesContract,
)
from butterfly.domain.entities.sales_order import SalesOrder, SalesOrderItem
from butterfly.infrastructure.memory.seed import CUSTOMERS, MATERIALS, USERS

STORY_START = date(2025, 9, 1)
FIRST_ORDER_NUMBER = 20001
CURRENCY = "INR"

CONTRACT_END = date(2026, 7, 12)
CONTRACT_RENEWED = date(2026, 9, 14)
SHORTAGE_START = date(2026, 7, 20)
SHORTAGE_END = date(2026, 8, 31)
SHORTAGE_KEEP = 3
SHORTAGE_OF = 5
SPOT_EVERY = 10
ACME_WEIGHT = Decimal("0.85")
CANCEL_EVERY = 16
NORMAL_WORKING_DAYS = 22
SETTLED_AFTER_DAYS = 30

ACME = 0
STEEL_PLATE = 1
BEARING = 4

QUANTITY_FACTOR = {
    "RM-1001": Decimal("1"),
    "RM-1002": Decimal("0.5"),
    "RM-1003": Decimal("1.5"),
    "RM-1004": Decimal("2"),
    "RM-1005": Decimal("12"),
    "RM-1006": Decimal("250"),
}

SUPPLIERS = [
    ("0000200001", "Doosan Metals Pvt Ltd"),
    ("0000200002", "Kalyani Wire Industries"),
    ("0000200003", "Precision Bearings Co"),
]

RAW_MATERIALS = [
    ("RAW-2001", "Steel billet", "KG", 0, "RM-1001"),
    ("RAW-2002", "Steel coil", "KG", 0, "RM-1002"),
    ("RAW-2003", "Copper rod", "KG", 1, "RM-1003"),
    ("RAW-2004", "Aluminium ingot", "KG", 1, "RM-1004"),
    ("RAW-2005", "Bearing steel", "KG", 2, "RM-1005"),
    ("RAW-2006", "Wire rod", "KG", 2, "RM-1006"),
]

ORDERED_QUANTITY = [Decimal("4000.000"), Decimal("5000.000"), Decimal("2000.000"), Decimal("1500.000"), Decimal("1000.000"), Decimal("3000.000")]
PLANNED_QUANTITY = [Decimal("3500.000"), Decimal("4000.000"), Decimal("1800.000"), Decimal("1400.000"), Decimal("900.000"), Decimal("2800.000")]
COMPONENT_MARGIN = Decimal("1.1")

PURCHASE_ORDER_BASE = 4500001146
PRODUCTION_ORDER_BASE = 1000356
BATCH_DAYS = 14
PURCHASE_LEAD_DAYS = 20

CUSTOMER_CONTRACTS = [
    [("0040000071", None, date(2024, 7, 13), date(2025, 7, 12), "8000000.00"), ("0040000127", "0040000071", date(2025, 7, 13), CONTRACT_END, "9000000.00"), ("0040000163", "0040000127", CONTRACT_RENEWED, date(2027, 9, 13), "10000000.00")],
    [("0040000101", None, date(2025, 4, 1), date(2026, 3, 31), "6000000.00"), ("0040000150", "0040000101", date(2026, 4, 1), date(2027, 3, 31), "6500000.00")],
    [("0040000102", None, date(2025, 1, 1), date(2025, 12, 31), "5000000.00"), ("0040000151", "0040000102", date(2026, 1, 1), date(2026, 12, 31), "5500000.00")],
    [("0040000103", None, date(2024, 10, 1), date(2025, 9, 30), "4200000.00"), ("0040000152", "0040000103", date(2025, 10, 1), date(2026, 9, 30), "4500000.00"), ("0040000160", "0040000152", date(2026, 10, 1), date(2027, 9, 30), "4800000.00")],
    [("0040000104", None, date(2025, 1, 15), date(2026, 1, 14), "5000000.00"), ("0040000153", "0040000104", date(2026, 1, 15), date(2027, 1, 14), "5200000.00")],
]

LATE_DELIVERIES = {(date(2026, 7, 1), "RAW-2002"): 12, (date(2026, 5, 1), "RAW-2003"): 4}
LATE_PRODUCTION = {
    (date(2026, 7, 1), "RM-1002"): (14, "MATERIAL_SHORTAGE"),
    (date(2026, 5, 1), "RM-1005"): (6, "MACHINE_BREAKDOWN"),
}


@dataclass(frozen=True)
class StorySeed:
    orders: list[SalesOrder]
    contracts: list[SalesContract]
    deliveries: list[PurchaseDelivery]
    production_orders: list[ProductionOrder]
    components: list[ProductionOrderComponent]


def build_story_seed(today: date) -> StorySeed:
    months = month_starts(today)
    planning_months = [*months, next_month(months[-1])]
    orders = build_orders(today)
    deliveries = build_deliveries(planning_months, today)
    production_orders, components = build_production(planning_months, today)
    return StorySeed(orders, build_contracts(today), deliveries, production_orders, components)


def next_month(day: date) -> date:
    return date(day.year + day.month // 12, day.month % 12 + 1, 1)


def month_starts(today: date) -> list[date]:
    first = date(today.year, today.month, 1)
    months = []
    day = STORY_START
    while day <= first:
        months.append(day)
        day = next_month(day)
    return months


def working_days(today: date) -> list[date]:
    days = (STORY_START + timedelta(days=offset) for offset in range((today - STORY_START).days + 1))
    return [day for day in days if day.weekday() < 5]


def month_factor(day: date) -> Decimal:
    first = date(day.year, day.month, 1)
    following = next_month(day)
    weekdays = sum(1 for offset in range((following - first).days) if (first + timedelta(days=offset)).weekday() < 5)
    return Decimal(NORMAL_WORKING_DAYS) / Decimal(weekdays)


def build_orders(today: date) -> list[SalesOrder]:
    orders: list[SalesOrder] = []
    for index, day in enumerate(working_days(today)):
        for customer_index in range(len(CUSTOMERS)):
            for copy in range(order_count(index, customer_index, day)):
                order = build_order(len(orders), index, day, customer_index, copy, today)
                if order:
                    orders.append(order)
    return orders


def order_count(index: int, customer_index: int, day: date) -> int:
    if customer_index == ACME and CONTRACT_END < day < CONTRACT_RENEWED:
        return 1 if index % SPOT_EVERY == 0 else 0
    if (index + customer_index) % 5 == 0:
        return 0
    return 2 if index % 7 == customer_index else 1


def keeps_item(material: str, index: int, customer_index: int, position: int, day: date) -> bool:
    if material != MATERIALS[STEEL_PLATE][0] or not SHORTAGE_START <= day <= SHORTAGE_END:
        return True
    return (index + customer_index + position) % SHORTAGE_OF < SHORTAGE_KEEP


def build_order(sequence: int, index: int, day: date, customer_index: int, copy: int, today: date) -> SalesOrder | None:
    number = f"{FIRST_ORDER_NUMBER + sequence:010d}"
    spot = customer_index == ACME and CONTRACT_END < day < CONTRACT_RENEWED
    item_count = 1 if spot else 2 + (index + customer_index) % 2
    items = []
    for position in range(item_count):
        material = MATERIALS[(index * 3 + customer_index * 2 + copy + position) % len(MATERIALS)]
        if not keeps_item(material[0], index, customer_index, position, day):
            continue
        items.append(build_item(number, len(items), material, index, customer_index, position, spot, month_factor(day)))
    if not items:
        return None
    customer_id, customer_name = CUSTOMERS[customer_index]
    created = datetime.combine(day, time(9, 0), timezone.utc) + timedelta(minutes=sequence % 480)
    return SalesOrder(
        sales_order=number,
        sales_order_type="OR",
        sold_to_party=customer_id,
        customer_name=customer_name,
        order_date=day,
        requested_delivery_date=day + timedelta(days=7),
        transaction_currency=CURRENCY,
        total_net_amount=sum((item.net_amount for item in items), Decimal("0.00")),
        overall_status=status_of(sequence, day, today),
        created_by_user=USERS[sequence % len(USERS)],
        creation_date_time=created,
        last_change_date_time=created,
        items=items,
    )


def build_item(number: str, position: int, material: tuple, index: int, customer_index: int, step: int, spot: bool, factor: Decimal) -> SalesOrderItem:
    material_id, description, unit, price = material
    steps = Decimal(10 * (1 + (index + customer_index + step) % 5))
    quantity = (steps * QUANTITY_FACTOR[material_id] * factor * (Decimal("0.5") if spot else 1) * (ACME_WEIGHT if customer_index == ACME else 1)).quantize(Decimal("0.001"))
    return SalesOrderItem(
        sales_order=number,
        sales_order_item=f"{(position + 1) * 10:06d}",
        material=material_id,
        material_description=description,
        quantity=quantity,
        quantity_unit=unit,
        net_amount=(quantity * price).quantize(Decimal("0.01")),
    )


def status_of(sequence: int, day: date, today: date) -> str:
    if sequence % CANCEL_EVERY == CANCEL_EVERY - 1:
        return "X"
    if (today - day).days > SETTLED_AFTER_DAYS:
        return "C"
    return ("A", "B", "C")[sequence % 3]


def build_contracts(today: date) -> list[SalesContract]:
    contracts = []
    for (customer_id, customer_name), history in zip(CUSTOMERS, CUSTOMER_CONTRACTS):
        for number, predecessor, valid_from, valid_to, value in history:
            if valid_from > today:
                continue
            contracts.append(
                SalesContract(number, predecessor, customer_id, customer_name, valid_from, valid_to, Decimal(value), CURRENCY, "A" if valid_to >= today else "E")
            )
    return contracts


def build_deliveries(months: list[date], today: date) -> list[PurchaseDelivery]:
    deliveries = []
    for month_index, month in enumerate(months):
        for raw_index, (material, description, unit, supplier_index, _) in enumerate(RAW_MATERIALS):
            promised = month + timedelta(days=13)
            ordered_on = promised - timedelta(days=PURCHASE_LEAD_DAYS)
            delay = LATE_DELIVERIES.get((month, material), (month_index + raw_index) % 3)
            actual = promised + timedelta(days=delay)
            delivered = actual <= today
            supplier_id, supplier_name = SUPPLIERS[supplier_index]
            deliveries.append(
                PurchaseDelivery(
                    purchase_order=str(PURCHASE_ORDER_BASE + month_index * len(RAW_MATERIALS) + raw_index),
                    purchase_order_item="00010",
                    supplier=supplier_id,
                    supplier_name=supplier_name,
                    material=material,
                    material_description=description,
                    order_date=ordered_on,
                    ordered_quantity=ORDERED_QUANTITY[raw_index],
                    delivered_quantity=ORDERED_QUANTITY[raw_index] if delivered else Decimal("0.000"),
                    quantity_unit=unit,
                    promised_delivery_date=promised,
                    actual_delivery_date=actual if delivered else None,
                    delivery_status="D" if delivered else "O",
                )
            )
    return deliveries


def build_production(months: list[date], today: date) -> tuple[list[ProductionOrder], list[ProductionOrderComponent]]:
    orders = []
    components = []
    last_end: dict[str, date] = {}
    for month_index, month in enumerate(months):
        for product_index, (product, description, unit, _) in enumerate(MATERIALS):
            planned_start = max(month + timedelta(days=5), last_end.get(product, STORY_START) + timedelta(days=1))
            planned_end = planned_start + timedelta(days=BATCH_DAYS)
            late_days, reason = LATE_PRODUCTION.get((month, product), (0, None))
            actual_end = planned_end + timedelta(days=late_days)
            last_end[product] = actual_end
            completed = actual_end <= today
            number = f"{PRODUCTION_ORDER_BASE + month_index * len(MATERIALS) + product_index:010d}"
            orders.append(
                ProductionOrder(
                    production_order=number,
                    material=product,
                    material_description=description,
                    planned_quantity=PLANNED_QUANTITY[product_index],
                    confirmed_quantity=PLANNED_QUANTITY[product_index] if completed else Decimal("0.000"),
                    quantity_unit=unit,
                    planned_start_date=planned_start,
                    planned_end_date=planned_end,
                    actual_end_date=actual_end if completed else None,
                    production_status="C" if completed else "R",
                    delay_reason=reason if completed else None,
                )
            )
            raw = RAW_MATERIALS[product_index]
            components.append(
                ProductionOrderComponent(number, raw[0], raw[1], (PLANNED_QUANTITY[product_index] * COMPONENT_MARGIN).quantize(Decimal("0.001")), raw[2])
            )
    return orders, components
