from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.compare import ChangeRow, Comparison
from synapse_api.domain.entities.registry import Registry
from synapse_api.domain.errors import InvalidQuery, MetricNotFound
from synapse_api.domain.gateways.metric_source import MetricSource

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


class CompareMetric:
    def __init__(self, source: MetricSource, registry: Registry):
        self.source = source
        self.registry = registry

    def execute(
        self, metric_name: str, start: date, end: date, compare_start: date, compare_end: date, by: str | None = None, top: int = 10
    ) -> list[Comparison]:
        metric = self.registry.metrics.get(metric_name)
        if metric is None:
            raise MetricNotFound()
        check_period(start, end)
        check_period(compare_start, compare_end)
        if by == "day" or by is not None and by not in metric.dimensions or not 1 <= top <= 50:
            raise InvalidQuery()
        if by is None:
            return self.totals_only(metric, start, end, compare_start, compare_end)
        splits = metric.dimensions[by].quantity is not None
        grouped: dict[str, dict[str, Totals]] = {}
        for is_current, (first, last) in ((True, (start, end)), (False, (compare_start, compare_end))):
            for row in self.source.rows(metric, by, first, last):
                entry = grouped.setdefault(row.currency, {}).setdefault(row.key, Totals(row.name, row.unit))
                quantity = row.quantity or Decimal(0)
                if is_current:
                    entry.current += row.amount
                    entry.quantity_current += quantity
                else:
                    entry.previous += row.amount
                    entry.quantity_previous += quantity
        return [self.comparison(currency, grouped[currency], splits, top) for currency in sorted(grouped)]

    def totals_only(self, metric, start: date, end: date, compare_start: date, compare_end: date) -> list[Comparison]:
        sums: dict[str, list[Decimal]] = {}
        for index, (first, last) in enumerate(((start, end), (compare_start, compare_end))):
            for row in self.source.rows(metric, "day", first, last):
                sums.setdefault(row.currency, [Decimal(0), Decimal(0)])[index] += row.amount
        return [
            Comparison(currency, cur, prev, cur - prev, percent(cur - prev, prev), None)
            for currency, (cur, prev) in sorted(sums.items())
        ]

    def comparison(self, currency: str, entries: dict[str, Totals], splits: bool, top: int) -> Comparison:
        current = sum((e.current for e in entries.values()), Decimal(0))
        previous = sum((e.previous for e in entries.values()), Decimal(0))
        change = current - previous
        rows = [self.row(key, e, change, splits) for key, e in entries.items()]
        rows.sort(key=lambda r: (-abs(r.change), r.key))
        kept, rest = rows[:top], rows[top:]
        if rest:
            kept.append(self.other(rest, change, splits))
        return Comparison(currency, current, previous, change, percent(change, previous), kept)

    def row(self, key: str, entry: Totals, total_change: Decimal, splits: bool) -> ChangeRow:
        change = entry.current - entry.previous
        share = percent(change, total_change)
        if not splits:
            return ChangeRow(key, entry.name, entry.current, entry.previous, change, share)
        price_previous = unit_price(entry.previous, entry.quantity_previous)
        volume = round_cents((entry.quantity_current - entry.quantity_previous) * price_previous) if price_previous else change
        return ChangeRow(
            key, entry.name, entry.current, entry.previous, change, share, entry.unit,
            entry.quantity_current, entry.quantity_previous,
            unit_price(entry.current, entry.quantity_current), price_previous,
            volume, change - volume,
        )

    def other(self, rows: list[ChangeRow], total_change: Decimal, splits: bool) -> ChangeRow:
        current = sum((r.current for r in rows), Decimal(0))
        previous = sum((r.previous for r in rows), Decimal(0))
        change = current - previous
        share = percent(change, total_change)
        if not splits:
            return ChangeRow("other", "Other", current, previous, change, share)
        volume = sum((r.volume_effect for r in rows), Decimal(0))
        return ChangeRow("other", "Other", current, previous, change, share, volume_effect=volume, price_effect=change - volume)


def unit_price(amount: Decimal, quantity: Decimal) -> Decimal | None:
    return (amount / quantity).quantize(Decimal("0.0001")) if quantity else None


def round_cents(value: Decimal) -> Decimal:
    return value.quantize(CENTS)
