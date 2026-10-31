from datetime import date, timedelta
from decimal import Decimal

from sami_agents.domain.entities.finding import Hit, MemberChange, Window


def day_of(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def percent(current: Decimal, previous: Decimal) -> Decimal | None:
    return ((current - previous) / previous * 100).quantize(Decimal("0.01")) if previous else None


def far_enough(current: Decimal, previous: Decimal, change: Decimal | None, minimum: float) -> bool:
    if change is None:
        return current > 0
    return abs(change) >= Decimal(str(minimum))


def later_than(rows: list[dict], params: dict, today: date) -> list[Hit]:
    hits = []
    for row in rows:
        due, done = day_of(row[params["due"]]), day_of(row[params["done"]])
        late = ((done or today) - due).days
        if late >= params["min_days"]:
            hits.append(Hit("later_than", due, {"days_late": late, "open": done is None}, [row]))
    return hits


def coverage_gap(rows: list[dict], params: dict, window: Window) -> list[Hit]:
    intervals = [(day_of(r[params["from"]]), day_of(r[params["to"]]) or window.end) for r in rows]
    covered = {d for first, last in intervals for d in days_between(first, last, window)}
    uncovered = [window.start + timedelta(days=n) for n in range(window.days) if window.start + timedelta(days=n) not in covered]
    if not uncovered:
        return []
    return [Hit("coverage_gap", uncovered[0], {"days_uncovered": len(uncovered), "first_uncovered": uncovered[0], "last_uncovered": uncovered[-1]}, rows)]


def days_between(first: date, last: date, window: Window) -> list[date]:
    low, high = max(first, window.start), min(last, window.end)
    return [low + timedelta(days=n) for n in range((high - low).days + 1)] if low <= high else []


def sum_changed(rows: list[dict], params: dict, window: Window) -> list[Hit]:
    now = [r for r in rows if window.start <= day_of(r[params["date"]]) <= window.end]
    before = [r for r in rows if window.compare_start <= day_of(r[params["date"]]) <= window.compare_end]
    current = sum((Decimal(r[params["field"]]) for r in now), Decimal(0))
    previous = sum((Decimal(r[params["field"]]) for r in before), Decimal(0))
    change = percent(current, previous)
    if not far_enough(current, previous, change, params["min_percent"]):
        return []
    return [Hit("sum_changed", None, {"current": current, "previous": previous, "change_percent": change}, now)]


def value_changed(change: MemberChange | None, params: dict) -> list[Hit]:
    if change is None or not far_enough(change.current, change.previous, change.change_percent, params["min_percent"]):
        return []
    numbers = {
        "current": change.current,
        "previous": change.previous,
        "change_percent": change.change_percent,
        "volume_effect": change.volume_effect,
        "price_effect": change.price_effect,
    }
    return [Hit("value_changed", None, numbers)]
