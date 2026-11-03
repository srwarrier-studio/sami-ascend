import bisect
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from butterfly.domain.entities.inventory import MaterialStock, StockMovement, StockValueMonth
from butterfly.domain.entities.master_data import USD_DIVISOR
from butterfly.infrastructure.memory.companies import CompanyProfile
from butterfly.infrastructure.memory.inventory_master import FINISHED_STORE, GROUP_OF, GROUPS, LOCATIONS, PLANTS, RAW_STORE
from butterfly.infrastructure.memory.story_seed import StorySeed

CURRENCY = "INR"
PRODUCT_COST_SHARE = Decimal("0.6")
REORDER_SHARE = Decimal("1.0")
BUFFERS = [Decimal(share) for share in ("0.2", "0.5", "1.0", "1.5", "2.0")]
WRITE_OFF_EVERY = 9
WRITE_OFF_OFFSET = 4
QUANTITY = Decimal("0.001")
MONEY = Decimal("0.01")
GROUP_NAMES = {group.code: group.name for group in GROUPS}
LOCATION_NAMES = {(location.plant, location.code): location.name for location in LOCATIONS}
ORDER_OF_TYPE = {"561": 0, "101": 1, "131": 1, "261": 2, "601": 2, "702": 3}
DIRECTION = {"561": "S", "101": "S", "131": "S", "261": "H", "601": "H", "702": "H"}


@dataclass(frozen=True)
class InventorySeed:
    stocks: list[MaterialStock]
    movements: list[StockMovement]
    monthly: list[StockValueMonth]


@dataclass(frozen=True)
class Item:
    company: str
    material: str
    description: str
    unit: str
    price: Decimal
    location: str


@dataclass(frozen=True)
class Event:
    day: date
    kind: str
    material: str
    quantity: Decimal


def items_of(companies: list[CompanyProfile]) -> dict[str, Item]:
    items = {}
    for company in companies:
        for material, description, unit, price in company.materials:
            items[material] = Item(company.code, material, description, unit, (price * PRODUCT_COST_SHARE).quantize(MONEY), FINISHED_STORE)
        for (material, description, unit, _, _, currency), price in zip(company.raw_materials, company.raw_price):
            items[material] = Item(company.code, material, description, unit, price * (USD_DIVISOR if currency == "USD" else 1), RAW_STORE)
    return items


def events_of(story: StorySeed, today: date) -> list[Event]:
    events = [
        Event(d.actual_delivery_date, "101", d.material, d.delivered_quantity)
        for d in story.deliveries
        if d.delivery_status != "X" and d.actual_delivery_date and d.actual_delivery_date <= today and d.delivered_quantity > 0
    ]
    events += [Event(p.actual_end_date, "131", p.material, p.confirmed_quantity) for p in story.production_orders if p.actual_end_date and p.actual_end_date <= today and p.confirmed_quantity > 0]
    started = {p.production_order: p.planned_start_date for p in story.production_orders if p.planned_start_date <= today}
    events += [Event(started[c.production_order], "261", c.material, c.required_quantity) for c in story.components if c.production_order in started]
    for order in story.orders:
        if order.overall_status == "X":
            continue
        shipped = order.requested_delivery_date or order.order_date
        events += [Event(shipped, "601", i.material, i.quantity) for i in order.items if shipped <= today]
    return sorted(events, key=lambda e: (e.day, ORDER_OF_TYPE[e.kind], e.material, e.quantity))


def signed(event: Event) -> Decimal:
    return event.quantity if DIRECTION[event.kind] == "S" else -event.quantity


def opening_of(material: str, events: list[Event]) -> Decimal:
    running, lowest = Decimal(0), Decimal(0)
    for event in events:
        running += signed(event)
        lowest = min(lowest, running)
    span = max((events[-1].day - events[0].day).days, 1) / Decimal("30.4")
    issues = sum((e.quantity for e in events if DIRECTION[e.kind] == "H"), Decimal(0))
    buffer = BUFFERS[sum(map(ord, material)) % len(BUFFERS)] * issues / span
    return (-lowest + buffer).quantize(QUANTITY)


def reorder_of(events: list[Event]) -> Decimal:
    span = max((events[-1].day - events[0].day).days, 1) / Decimal("30.4")
    issues = sum((e.quantity for e in events if DIRECTION[e.kind] == "H"), Decimal(0))
    return (REORDER_SHARE * issues / span).quantize(QUANTITY)


def build_inventory(story: StorySeed, companies: list[CompanyProfile], today: date) -> InventorySeed:
    items = items_of(companies)
    by_material: dict[str, list[Event]] = {}
    for event in events_of(story, today):
        by_material.setdefault(event.material, []).append(event)
    ordered = sorted(by_material)
    for index, material in enumerate(ordered):
        events = by_material[material]
        start = events[0].day - timedelta(days=1)
        opening = Event(start, "561", material, opening_of(material, events))
        by_material[material] = [opening, *events]
        if index % WRITE_OFF_EVERY == WRITE_OFF_OFFSET:
            left = sum((signed(e) for e in by_material[material]), Decimal(0))
            by_material[material].append(Event(today, "702", material, left))
    reorder = {material: reorder_of(events[1:]) for material, events in by_material.items()}
    return InventorySeed(*assemble(items, by_material, reorder, today))


def assemble(items: dict[str, Item], by_material: dict[str, list[Event]], reorder: dict[str, Decimal], today: date):
    movements = number_movements(items, [event for events in by_material.values() for event in events])
    stocks = []
    for material, events in sorted(by_material.items()):
        item = items[material]
        quantity = sum((signed(e) for e in events), Decimal(0)).quantize(QUANTITY)
        plant = PLANTS[item.company]
        stocks.append(
            MaterialStock(
                material, item.description, GROUP_OF[material], GROUP_NAMES[GROUP_OF[material]], plant, item.location, LOCATION_NAMES[(plant, item.location)],
                quantity, item.unit, (quantity * item.price).quantize(MONEY), CURRENCY, reorder[material], max(e.day for e in events), item.company,
            )
        )
    return stocks, movements, month_end_values(items, by_material, today)


def number_movements(items: dict[str, Item], events: list[Event]) -> list[StockMovement]:
    movements = []
    for number, event in enumerate(sorted(events, key=lambda e: (e.day, ORDER_OF_TYPE[e.kind], e.material)), start=1):
        item = items[event.material]
        stamp = datetime.combine(event.day, time(8 + number * 7 % 10, number * 13 % 60), timezone.utc)
        movements.append(
            StockMovement(
                f"{4900000000 + number:010d}", "0001", str(event.day.year), event.day, stamp, event.material, item.description, PLANTS[item.company], item.location,
                event.kind, DIRECTION[event.kind], event.quantity, item.unit, (event.quantity * item.price).quantize(MONEY), CURRENCY, item.company,
            )
        )
    return movements


def month_end_values(items: dict[str, Item], by_material: dict[str, list[Event]], today: date) -> list[StockValueMonth]:
    first = min(events[0].day for events in by_material.values())
    months = []
    day = date(first.year, first.month, 1)
    while day <= today:
        months.append(day)
        day = date(day.year + day.month // 12, day.month % 12 + 1, 1)
    totals: dict[tuple[str, int], Decimal] = {}
    for material, events in by_material.items():
        days = [e.day for e in events]
        running, total = [], Decimal(0)
        for event in events:
            total += signed(event)
            running.append(total)
        for index, month in enumerate(months):
            end = today if month.month == today.month and month.year == today.year else date(month.year + month.month // 12, month.month % 12 + 1, 1) - timedelta(days=1)
            position = bisect.bisect_right(days, end)
            quantity = running[position - 1] if position else Decimal(0)
            key = (items[material].company, index)
            totals[key] = totals.get(key, Decimal(0)) + quantity * items[material].price
    return [
        StockValueMonth(f"{months[index].year}-{months[index].month:02d}", value.quantize(MONEY), CURRENCY, company)
        for (company, index), value in sorted(totals.items(), key=lambda entry: (entry[0][0], entry[0][1]))
    ]
