from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.compare import ChangeRow, Comparison
from synapse_api.domain.errors import InvalidQuery
from synapse_api.domain.gateways.sales_source import SalesSource

MAX_DAYS = 400
CENTS = Decimal("0.01")


@dataclass
class Totals:
    name: str = ""
    unit: str | None = None
    current: Decimal = Decimal(0)
    previous: Decimal = Decimal(0)
    quantity_current: Decimal = Decimal(0)
    quantity_previous: Decimal = Decimal(0)


def check_period(start: date, end: date) -> None:
    if start > end or (end - start).days + 1 > MAX_DAYS:
        raise InvalidQuery()


def percent(part: Decimal, whole: Decimal) -> Decimal | None:
    return (part / whole * 100).quantize(CENTS) if whole else None


class CompareSales:
    def __init__(self, source: SalesSource):
        self.source = source

    def execute(
        self, start: date, end: date, compare_start: date, compare_end: date, by: str | None = None, top: int = 10
    ) -> list[Comparison]:
        check_period(start, end)
        check_period(compare_start, compare_end)
        if by not in (None, "customer", "material") or not 1 <= top <= 50:
            raise InvalidQuery()
        if by is None:
            return self.totals_only(start, end, compare_start, compare_end)
        grouped: dict[str, dict[str, Totals]] = {}
        for is_current, (first, last) in ((True, (start, end)), (False, (compare_start, compare_end))):
            for row in self.read(by, first, last):
                key, name, unit, quantity = self.fields(by, row)
                entry = grouped.setdefault(row.currency, {}).setdefault(key, Totals(name, unit))
                if is_current:
                    entry.current += row.net_amount
                    entry.quantity_current += quantity
                else:
                    entry.previous += row.net_amount
                    entry.quantity_previous += quantity
        return [self.comparison(currency, grouped[currency], by, top) for currency in sorted(grouped)]

    def totals_only(self, start: date, end: date, compare_start: date, compare_end: date) -> list[Comparison]:
        sums: dict[str, list[Decimal]] = {}
        for index, (first, last) in enumerate(((start, end), (compare_start, compare_end))):
            for row in self.source.daily_sales(first, last):
                sums.setdefault(row.currency, [Decimal(0), Decimal(0)])[index] += row.net_amount
        return [
            Comparison(currency, cur, prev, cur - prev, percent(cur - prev, prev), None)
            for currency, (cur, prev) in sorted(sums.items())
        ]

    def read(self, by: str, first: date, last: date) -> list:
        if by == "customer":
            return self.source.customer_sales(first, last)
        return self.source.material_sales(first, last)

    def fields(self, by: str, row) -> tuple[str, str, str | None, Decimal]:
        if by == "customer":
            return row.customer, row.name, None, Decimal(0)
        return row.material, row.description, row.unit, row.quantity

    def comparison(self, currency: str, entries: dict[str, Totals], by: str, top: int) -> Comparison:
        current = sum((e.current for e in entries.values()), Decimal(0))
        previous = sum((e.previous for e in entries.values()), Decimal(0))
        change = current - previous
        rows = [self.row(key, e, change, by) for key, e in entries.items()]
        rows.sort(key=lambda r: (-abs(r.change), r.key))
        kept, rest = rows[:top], rows[top:]
        if rest:
            kept.append(self.other(rest, change, by))
        return Comparison(currency, current, previous, change, percent(change, previous), kept)

    def row(self, key: str, entry: Totals, total_change: Decimal, by: str) -> ChangeRow:
        change = entry.current - entry.previous
        share = percent(change, total_change)
        if by == "customer":
            return ChangeRow(key, entry.name, entry.current, entry.previous, change, share)
        price_previous = unit_price(entry.previous, entry.quantity_previous)
        volume = round_cents((entry.quantity_current - entry.quantity_previous) * price_previous) if price_previous else change
        return ChangeRow(
            key, entry.name, entry.current, entry.previous, change, share, entry.unit,
            entry.quantity_current, entry.quantity_previous,
            unit_price(entry.current, entry.quantity_current), price_previous,
            volume, change - volume,
        )

    def other(self, rows: list[ChangeRow], total_change: Decimal, by: str) -> ChangeRow:
        current = sum((r.current for r in rows), Decimal(0))
        previous = sum((r.previous for r in rows), Decimal(0))
        change = current - previous
        share = percent(change, total_change)
        if by == "customer":
            return ChangeRow("other", "Other", current, previous, change, share)
        volume = sum((r.volume_effect for r in rows), Decimal(0))
        return ChangeRow("other", "Other", current, previous, change, share, volume_effect=volume, price_effect=change - volume)


def unit_price(amount: Decimal, quantity: Decimal) -> Decimal | None:
    return (amount / quantity).quantize(Decimal("0.0001")) if quantity else None


def round_cents(value: Decimal) -> Decimal:
    return value.quantize(CENTS)
