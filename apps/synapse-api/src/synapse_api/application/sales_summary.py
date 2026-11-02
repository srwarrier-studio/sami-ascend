import calendar
from datetime import date
from decimal import Decimal

from synapse_api.application.sales_widgets import month_note, month_periods, range_label, sales_in
from synapse_api.domain.gateways.sales_source import SalesSource

SYMBOLS = {"INR": "₹", "USD": "$", "EUR": "€"}


def money(amount: Decimal, currency: str) -> str:
    whole = int(round(abs(amount)))
    digits = str(whole)
    if currency == "INR" and len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        digits = ",".join([head, *groups, tail] if head else [*groups, tail])
    else:
        digits = f"{whole:,}"
    return f"{SYMBOLS.get(currency, currency + ' ')}{digits}"


def customer_totals(source: SalesSource, period: tuple[date, date], currency: str) -> dict[str, tuple[str, Decimal]]:
    totals: dict[str, tuple[str, Decimal]] = {}
    for row in source.customer_sales(*period):
        if row.currency == currency:
            name, amount = totals.get(row.customer, (row.name, Decimal(0)))
            totals[row.customer] = (name, amount + row.net_amount)
    return totals


class GetSalesSummary:
    def __init__(self, source: SalesSource, target: Decimal):
        self.source = source
        self.target = target

    def execute(self, today: date, currency: str) -> list[str]:
        current, previous = month_periods(today)
        now, _ = sales_in(self.source, current, currency)
        before, _ = sales_in(self.source, previous, currency)
        sentences = [self.headline(today, current, previous, now, before, currency)]
        mover = self.mover(current, previous, currency)
        if mover:
            sentences.append(mover)
        target = self.pace(today, now, currency)
        if target:
            sentences.append(target)
        return [sentence for sentence in sentences if sentence]

    def headline(self, today: date, current, previous, now: Decimal, before: Decimal, currency: str) -> str | None:
        if now == 0 and before == 0:
            return None
        note = month_note(today)
        days = f"{range_label(current)}, {note}" if note else range_label(current)
        if before == 0:
            return f"Sales this month are {money(now, currency)} ({days}); there were none on the same days last month."
        change = (now - before) / before
        way = "up" if change >= 0 else "down"
        return f"Sales this month are {money(now, currency)} ({days}), {way} {abs(change) * 100:.1f}% on {range_label(previous)}."

    def mover(self, current, previous, currency: str) -> str | None:
        now = customer_totals(self.source, current, currency)
        before = customer_totals(self.source, previous, currency)
        changes = {key: (now.get(key, before.get(key))[0], now.get(key, ("", Decimal(0)))[1] - before.get(key, ("", Decimal(0)))[1]) for key in {*now, *before}}
        if not changes:
            return None
        name, change = max(changes.values(), key=lambda item: (abs(item[1]), item[0]))
        if change == 0:
            return None
        return f"{name} moved most: {money(change, currency)} {'more' if change > 0 else 'less'} than on {range_label(previous)}."

    def pace(self, today: date, now: Decimal, currency: str) -> str | None:
        if self.target <= 0:
            return None
        reached = float(now / self.target) * 100
        gone = today.day / calendar.monthrange(today.year, today.month)[1] * 100
        way = "behind" if reached < gone else "ahead of"
        return f"{reached:.0f}% of the {money(self.target, currency)} monthly target is reached with {gone:.0f}% of the month gone, so sales are {way} the pace."
