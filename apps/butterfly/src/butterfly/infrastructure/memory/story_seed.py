from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from butterfly.domain.entities.drivers import (
    CustomerInvoice,
    ProductionOrder,
    ProductionOrderComponent,
    PurchaseDelivery,
    SalesContract,
)
from butterfly.domain.entities.sales_order import SalesOrder, SalesOrderItem
from butterfly.domain.entities.scenario import (
    Cancellations,
    ContractEnd,
    CustomerLoss,
    DemandGrowth,
    Drop,
    PriceChange,
    ProductionDelay,
    PurchasePriceChange,
    PurchaseQuantityChange,
    Scenario,
    SupplierSwitch,
    SupplyDelay,
)
from butterfly.infrastructure.memory.scenarios import AUGUST_CONTRACT
from butterfly.infrastructure.memory.invoices import build_invoices
from butterfly.infrastructure.memory.seed import CUSTOMERS, MATERIALS, USERS

STORY_START = date(2025, 9, 1)
FIRST_ORDER_NUMBER = 20001
CURRENCY = "INR"

SPOT_EVERY = 10
ACME_WEIGHT = Decimal("1")
OTHER_WEIGHT = Decimal("0.95")
CANCEL_EVERY = 16
NORMAL_WORKING_DAYS = 22
SETTLED_AFTER_DAYS = 30

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
RAW_PRICE = [Decimal("46.00"), Decimal("52.00"), Decimal("610.00"), Decimal("190.00"), Decimal("70.00"), Decimal("48.00")]
COMPONENT_MARGIN = Decimal("1.1")

PURCHASE_ORDER_BASE = 4500001146
PRODUCTION_ORDER_BASE = 1000356
BATCH_DAYS = 14
PURCHASE_LEAD_DAYS = 20

CUSTOMER_CONTRACTS = [
    [("0040000071", None, date(2024, 7, 13), date(2025, 7, 12), "8000000.00"), ("0040000127", "0040000071", date(2025, 7, 13), date(2026, 7, 12), "9000000.00"), ("0040000163", "0040000127", date(2026, 7, 13), date(2027, 7, 12), "10000000.00")],
    [("0040000101", None, date(2025, 4, 1), date(2026, 3, 31), "6000000.00"), ("0040000150", "0040000101", date(2026, 4, 1), date(2027, 3, 31), "6500000.00")],
    [("0040000102", None, date(2025, 1, 1), date(2025, 12, 31), "5000000.00"), ("0040000151", "0040000102", date(2026, 1, 1), date(2026, 12, 31), "5500000.00")],
    [("0040000103", None, date(2024, 10, 1), date(2025, 9, 30), "4200000.00"), ("0040000152", "0040000103", date(2025, 10, 1), date(2026, 9, 30), "4500000.00"), ("0040000160", "0040000152", date(2026, 10, 1), date(2027, 9, 30), "4800000.00")],
    [("0040000104", None, date(2025, 1, 15), date(2026, 1, 14), "5000000.00"), ("0040000153", "0040000104", date(2026, 1, 15), date(2027, 1, 14), "5200000.00")],
]

@dataclass(frozen=True)
class StorySeed:
    orders: list[SalesOrder]
    contracts: list[SalesContract]
    deliveries: list[PurchaseDelivery]
    production_orders: list[ProductionOrder]
    components: list[ProductionOrderComponent]
    invoices: list[CustomerInvoice]


def build_story_seed(today: date, scenario: Scenario = AUGUST_CONTRACT) -> StorySeed:
    months = month_starts(today)
    planning_months = [*months, next_month(months[-1])]
    orders = build_orders(today, scenario)
    deliveries = build_deliveries(planning_months, today, scenario)
    production_orders, components = build_production(planning_months, today, scenario)
    return StorySeed(orders, build_contracts(today, scenario), deliveries, production_orders, components, build_invoices(orders, today))


def events_of(scenario: Scenario, kind: type) -> list:
    return [event for event in scenario.events if isinstance(event, kind)]


def contract_gap(scenario: Scenario, customer_index: int, day: date) -> ContractEnd | None:
    for end in events_of(scenario, ContractEnd):
        if end.customer == customer_index and end.last_valid < day < (end.renewal or date.max):
            return end
    return None


def drops_of(scenario: Scenario) -> list[Drop]:
    delays = [*events_of(scenario, SupplyDelay), *events_of(scenario, ProductionDelay)]
    return [delay.drop for delay in delays if delay.drop]


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


def build_orders(today: date, scenario: Scenario) -> list[SalesOrder]:
    orders: list[SalesOrder] = []
    for index, day in enumerate(working_days(today)):
        for customer_index in range(len(CUSTOMERS)):
            for copy in range(order_count(index, customer_index, day, scenario)):
                order = build_order(len(orders), index, day, customer_index, copy, today, scenario)
                if order:
                    orders.append(order)
    return orders


def order_count(index: int, customer_index: int, day: date, scenario: Scenario) -> int:
    if any(loss.customer == customer_index and day >= loss.start for loss in events_of(scenario, CustomerLoss)):
        return 0
    gap = contract_gap(scenario, customer_index, day)
    if gap:
        return 1 if gap.spot and index % SPOT_EVERY == 0 else 0
    if (index + customer_index) % 5 == 0:
        return 0
    return 2 if index % 7 == customer_index else 1


def keeps_item(material: str, index: int, customer_index: int, position: int, day: date, scenario: Scenario) -> bool:
    for drop in drops_of(scenario):
        applies = drop.material == material and drop.start <= day <= drop.end and (drop.customers is None or customer_index in drop.customers)
        if applies and (index + customer_index + position) % drop.of >= drop.keep:
            return False
    return True


def price_factor(material: str, day: date, scenario: Scenario) -> Decimal:
    factor = Decimal(1)
    for change in events_of(scenario, PriceChange):
        if change.material == material and day >= change.start:
            factor *= Decimal(change.factor)
    return factor


def growth_factor(material: str, day: date, scenario: Scenario) -> Decimal:
    factor = Decimal(1)
    for growth in events_of(scenario, DemandGrowth):
        if growth.material == material and day >= growth.start:
            factor *= Decimal(growth.factor)
    return factor


def months_after(day: date, count: int) -> date:
    first = date(day.year, day.month, 1)
    for _ in range(count):
        first = next_month(first)
    return first


def production_growth(material: str, month: date, scenario: Scenario) -> Decimal:
    factor = Decimal(1)
    for growth in events_of(scenario, DemandGrowth):
        if growth.material == material and month >= months_after(growth.start, 1):
            factor *= Decimal(growth.factor)
    return factor


def purchase_growth(product: str, ordered_on: date, scenario: Scenario) -> Decimal:
    factor = Decimal(1)
    for growth in events_of(scenario, DemandGrowth):
        if growth.material == product and ordered_on >= months_after(growth.start, 2):
            factor *= Decimal(growth.factor)
    return factor


def is_cancelled(sequence: int, day: date, customer_index: int, scenario: Scenario) -> bool:
    return any(
        c.customer == customer_index and c.start <= day <= c.end and sequence % c.of < c.cancelled
        for c in events_of(scenario, Cancellations)
    )


def build_order(sequence: int, index: int, day: date, customer_index: int, copy: int, today: date, scenario: Scenario) -> SalesOrder | None:
    number = f"{FIRST_ORDER_NUMBER + sequence:010d}"
    gap = contract_gap(scenario, customer_index, day)
    spot = bool(gap and gap.spot)
    item_count = 1 if spot else 2 + (index + customer_index) % 2
    items = []
    for position in range(item_count):
        material = MATERIALS[(index * 3 + customer_index * 2 + copy + position) % len(MATERIALS)]
        if not keeps_item(material[0], index, customer_index, position, day, scenario):
            continue
        items.append(build_item(number, len(items), material, index, customer_index, position, spot, month_factor(day), price_factor(material[0], day, scenario), growth_factor(material[0], day, scenario)))
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
        overall_status="X" if is_cancelled(sequence, day, customer_index, scenario) else status_of(sequence, day, today),
        created_by_user=USERS[sequence % len(USERS)],
        creation_date_time=created,
        last_change_date_time=created,
        items=items,
    )


def build_item(number: str, position: int, material: tuple, index: int, customer_index: int, step: int, spot: bool, factor: Decimal, price_change: Decimal, growth: Decimal) -> SalesOrderItem:
    material_id, description, unit, price = material
    steps = Decimal(10 * (1 + (index + customer_index + step) % 5))
    quantity = (steps * QUANTITY_FACTOR[material_id] * factor * growth * (Decimal("0.5") if spot else 1) * (ACME_WEIGHT if customer_index == 0 else OTHER_WEIGHT)).quantize(Decimal("0.001"))
    return SalesOrderItem(
        sales_order=number,
        sales_order_item=f"{(position + 1) * 10:06d}",
        material=material_id,
        material_description=description,
        quantity=quantity,
        quantity_unit=unit,
        net_amount=(quantity * price * price_change).quantize(Decimal("0.01")),
    )


def status_of(sequence: int, day: date, today: date) -> str:
    if sequence % CANCEL_EVERY == CANCEL_EVERY - 1:
        return "X"
    if (today - day).days > SETTLED_AFTER_DAYS:
        return "C"
    return ("A", "B", "C")[sequence % 3]


def contract_history(customer_index: int, scenario: Scenario) -> list[tuple]:
    history = list(CUSTOMER_CONTRACTS[customer_index])
    for end in events_of(scenario, ContractEnd):
        if end.customer != customer_index:
            continue
        history = [(n, p, f, min(t, end.last_valid), v) for n, p, f, t, v in history if f <= end.last_valid]
        if end.renewal:
            number, _, _, valid_to, value = history[-1]
            renewed_to = end.renewal.replace(year=end.renewal.year + 1) - timedelta(days=1)
            history.append((end.renewal_contract, number, end.renewal, renewed_to, str(Decimal(value) + Decimal("1000000"))))
    return history


def build_contracts(today: date, scenario: Scenario) -> list[SalesContract]:
    contracts = []
    for index, (customer_id, customer_name) in enumerate(CUSTOMERS):
        for number, predecessor, valid_from, valid_to, value in contract_history(index, scenario):
            if valid_from > today:
                continue
            contracts.append(
                SalesContract(number, predecessor, customer_id, customer_name, valid_from, valid_to, Decimal(value), CURRENCY, "A" if valid_to >= today else "E")
            )
    return contracts


def build_deliveries(months: list[date], today: date, scenario: Scenario) -> list[PurchaseDelivery]:
    late = {(delay.month, delay.raw_material): delay.days for delay in events_of(scenario, SupplyDelay)}
    deliveries = []
    for month_index, month in enumerate(months):
        for raw_index, (material, description, unit, supplier_index, _) in enumerate(RAW_MATERIALS):
            promised = month + timedelta(days=13)
            ordered_on = promised - timedelta(days=PURCHASE_LEAD_DAYS)
            delay = late.get((month, material), (month_index + raw_index) % 3)
            actual = promised + timedelta(days=delay)
            delivered = actual <= today
            quantity, price = ORDERED_QUANTITY[raw_index], RAW_PRICE[raw_index]
            product = RAW_MATERIALS[raw_index][4]
            quantity = (quantity * purchase_growth(product, ordered_on, scenario)).quantize(Decimal("0.001"))
            for change in events_of(scenario, PurchaseQuantityChange):
                if change.raw_material == material and change.start <= ordered_on <= change.end:
                    quantity = (quantity * Decimal(change.factor)).quantize(Decimal("0.001"))
            for change in events_of(scenario, PurchasePriceChange):
                if change.raw_material == material and ordered_on >= change.start:
                    price *= Decimal(change.factor)
            for switch in events_of(scenario, SupplierSwitch):
                if switch.raw_material == material and ordered_on >= switch.start:
                    supplier_index = switch.supplier
                    price *= Decimal(switch.price_factor)
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
                    ordered_quantity=quantity,
                    delivered_quantity=quantity if delivered else Decimal("0.000"),
                    quantity_unit=unit,
                    promised_delivery_date=promised,
                    actual_delivery_date=actual if delivered else None,
                    delivery_status="D" if delivered else "O",
                    net_amount=(quantity * price).quantize(Decimal("0.01")),
                )
            )
    return deliveries


def build_production(months: list[date], today: date, scenario: Scenario) -> tuple[list[ProductionOrder], list[ProductionOrderComponent]]:
    late = {(delay.month, delay.material): (delay.days, delay.reason) for delay in events_of(scenario, ProductionDelay)}
    orders = []
    components = []
    last_end: dict[str, date] = {}
    for month_index, month in enumerate(months):
        for product_index, (product, description, unit, _) in enumerate(MATERIALS):
            planned_start = max(month + timedelta(days=5), last_end.get(product, STORY_START) + timedelta(days=1))
            planned_end = planned_start + timedelta(days=BATCH_DAYS)
            late_days, reason = late.get((month, product), (0, None))
            actual_end = planned_end + timedelta(days=late_days)
            last_end[product] = actual_end
            completed = actual_end <= today
            number = f"{PRODUCTION_ORDER_BASE + month_index * len(MATERIALS) + product_index:010d}"
            planned = (PLANNED_QUANTITY[product_index] * production_growth(product, month, scenario)).quantize(Decimal("0.001"))
            orders.append(
                ProductionOrder(
                    production_order=number,
                    material=product,
                    material_description=description,
                    planned_quantity=planned,
                    confirmed_quantity=planned if completed else Decimal("0.000"),
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
                ProductionOrderComponent(number, raw[0], raw[1], (planned * COMPONENT_MARGIN).quantize(Decimal("0.001")), raw[2])
            )
    return orders, components
