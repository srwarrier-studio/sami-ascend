from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from butterfly.domain.entities.drivers import ProductionOrder
from butterfly.domain.entities.production import ProductionConfirmation, WorkCenterDowntime
from butterfly.infrastructure.memory.companies import CompanyProfile
from butterfly.infrastructure.memory.inventory_master import PLANTS
from butterfly.infrastructure.memory.inventory_seed import CURRENCY, MONEY, QUANTITY, items_of
from butterfly.infrastructure.memory.production_master import LINES, SCRAP_REASONS, SHIFTS
from butterfly.infrastructure.memory.story_seed import StorySeed

HOURS = Decimal("0.01")
RUN_HOURS = Decimal("8.00")
CHANGEOVER_HOURS = Decimal("2.00")
OTHER_HOURS = Decimal("1.50")
LATE_DAY_HOURS = 8
DELAY_CAUSES = {"MACHINE_BREAKDOWN": "BREAKDOWN", "MATERIAL_SHORTAGE": "NO_MATERIAL"}
MAINTENANCE_DAY = 10
SUNDAY = 6


@dataclass(frozen=True)
class ProductionSeed:
    confirmations: list[ProductionConfirmation]
    downtimes: list[WorkCenterDowntime]


@dataclass(frozen=True)
class Draft:
    order: ProductionOrder
    day: date
    line: int
    shift: str
    yield_quantity: Decimal
    scrap_quantity: Decimal
    target_quantity: Decimal
    reason: str | None


def working_days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=n) for n in range((end - start).days + 1) if (start + timedelta(days=n)).weekday() != SUNDAY]


def spread(total: Decimal, weights: list[int]) -> list[Decimal]:
    whole = sum(weights)
    parts = [(total * weight / whole).quantize(QUANTITY) for weight in weights[:-1]]
    return [*parts, (total - sum(parts, Decimal(0))).quantize(QUANTITY)]


def drafts_of(order: ProductionOrder, today: date) -> list[Draft]:
    if order.actual_end_date is None or order.confirmed_quantity <= 0 or order.planned_start_date > today:
        return []
    days = working_days(order.planned_start_date, order.actual_end_date)
    number = int(order.production_order)
    weights = [100 + (index * 7 + number) % 5 * 4 - 8 for index in range(len(days))]
    yields = spread(order.confirmed_quantity, weights)
    targets = spread(order.planned_quantity, [1] * len(days))
    rate = Decimal(5 + number * 13 % 36) / Decimal(1000)
    drafts = []
    for index, day in enumerate(days):
        clean = (number * 3 + index) % 11 == 0
        scrap = Decimal(0) if clean else (yields[index] * rate).quantize(QUANTITY)
        reason = None if clean else SCRAP_REASONS[(number + index) % len(SCRAP_REASONS)]
        drafts.append(Draft(order, day, number % LINES + 1, SHIFTS[(number + index) % len(SHIFTS)], yields[index], scrap, targets[index], reason))
    return drafts


def build_production(story: StorySeed, companies: list[CompanyProfile], today: date) -> ProductionSeed:
    items = items_of(companies)
    drafts = sorted((draft for order in story.production_orders for draft in drafts_of(order, today)), key=lambda d: (d.day, d.order.production_order))
    confirmations = []
    for sequence, draft in enumerate(drafts, start=1):
        order = draft.order
        item = items[order.material]
        confirmations.append(
            ProductionConfirmation(
                f"{8000000000 + sequence:010d}", "00000001", order.production_order, order.material, order.material_description, PLANTS[order.company_code],
                f"LINE{draft.line}", f"Line {draft.line}", draft.shift, draft.day, draft.yield_quantity, draft.scrap_quantity, draft.target_quantity, order.quantity_unit,
                draft.reason, RUN_HOURS, (draft.yield_quantity * item.price).quantize(MONEY), (draft.scrap_quantity * item.price).quantize(MONEY),
                (draft.target_quantity * item.price).quantize(MONEY), CURRENCY, order.company_code,
            )
        )
    return ProductionSeed(confirmations, number_downtimes(downtimes_of(story, drafts)))


def downtimes_of(story: StorySeed, drafts: list[Draft]) -> list[tuple]:
    by_order: dict[str, list[Draft]] = {}
    for draft in drafts:
        by_order.setdefault(draft.order.production_order, []).append(draft)
    events = []
    for number, days in by_order.items():
        order = days[0].order
        line = days[0].line
        events.append((days[0].day, order, line, CHANGEOVER_HOURS, "CHANGEOVER"))
        late = (order.actual_end_date - order.planned_end_date).days
        if late > 0 and order.delay_reason:
            on_time = [d for d in days if d.day <= order.planned_end_date]
            events.append((on_time[-1].day if on_time else days[0].day, order, line, Decimal(late * LATE_DAY_HOURS).quantize(HOURS), DELAY_CAUSES.get(order.delay_reason, "OTHER")))
        if int(number) % 8 == 3:
            events.append((days[len(days) // 2].day, order, line, OTHER_HOURS, "OTHER"))
    lines: dict[tuple[str, int, int, int], list[Draft]] = {}
    for draft in drafts:
        lines.setdefault((draft.order.company_code, draft.line, draft.day.year, draft.day.month), []).append(draft)
    for (company, line, year, month), group in sorted(lines.items()):
        after = [d for d in group if d.day.day >= MAINTENANCE_DAY]
        chosen = min(after, key=lambda d: (d.day, d.order.production_order)) if after else max(group, key=lambda d: (d.day, d.order.production_order))
        events.append((chosen.day, chosen.order, line, Decimal(4 + line).quantize(HOURS), "MAINTENANCE"))
    return events


def number_downtimes(events: list[tuple]) -> list[WorkCenterDowntime]:
    ordered = sorted(events, key=lambda e: (e[0], e[1].production_order, e[4]))
    return [
        WorkCenterDowntime(f"{45000 + sequence:010d}", order.production_order, PLANTS[order.company_code], f"LINE{line}", f"Line {line}", day, hours, cause, order.company_code)
        for sequence, (day, order, line, hours, cause) in enumerate(ordered, start=1)
    ]
