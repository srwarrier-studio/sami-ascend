from datetime import date, timedelta
from decimal import Decimal

from synapse_api.application.inventory_widgets import STATUS_NAMES, month_values, period_of, stock_value
from synapse_api.application.sales_summary import money
from synapse_api.application.sales_widgets import MONTH_NAMES
from synapse_api.domain.gateways.inventory_source import InventorySource

INVENTORY_IDS = {"inv-value", "inv-low", "inv-availability", "inv-warehouses", "inv-groups", "inv-slow", "inv-movement", "inv-reorder", "inv-heat"}


class GetInventorySummary:
    def __init__(self, source: InventorySource):
        self.source = source

    def execute(self, today: date, currency: str, show: set[str]) -> list[str]:
        sentences = [self.opening(today, currency)]
        if show & {"inv-low", "inv-reorder"}:
            sentences.append(self.reorder(currency))
        if "inv-groups" in show:
            sentences.append(self.biggest_group(currency))
        if "inv-slow" in show:
            sentences.append(self.idle(today, currency))
        return [sentence for sentence in sentences if sentence]

    def opening(self, today: date, currency: str) -> str | None:
        now = stock_value(self.source, currency)
        if now <= 0:
            return None
        last_month_end = today.replace(day=1) - timedelta(days=1)
        before = month_values(self.source, today, currency).get(period_of(last_month_end), Decimal(0))
        if before <= 0:
            return f"Stock is worth {money(now, currency)}."
        change = (now - before) / before
        return f"Stock is worth {money(now, currency)}, {'up' if change >= 0 else 'down'} {abs(change) * 100:.1f}% on the end of {MONTH_NAMES[last_month_end.month - 1]}."

    def reorder(self, currency: str) -> str | None:
        rows = [row for row in self.source.stock_by_status() if row.currency == currency]
        low = sum(row.count for row in rows if row.status in STATUS_NAMES)
        out = sum(row.count for row in rows if row.status == "Z")
        if low == 0:
            return None
        if low == 1:
            return "1 item is below its reorder level" + (" and is out of stock." if out else ".")
        return f"{low} items are below their reorder level, {out} of them out of stock." if out else f"{low} items are below their reorder level."

    def biggest_group(self, currency: str) -> str | None:
        totals: dict[str, tuple[str, Decimal]] = {}
        for row in self.source.stock_by_group():
            if row.currency == currency:
                name, value = totals.get(row.group, (row.name, Decimal(0)))
                totals[row.group] = (name, value + row.value)
        whole = sum((value for _, value in totals.values()), Decimal(0))
        if whole <= 0:
            return None
        name, value = max(totals.values(), key=lambda item: (item[1], item[0]))
        return f"{name} holds the most stock: {money(value, currency)} ({value / whole * 100:.0f}% of its value)."

    def idle(self, today: date, currency: str) -> str | None:
        items = [item for item in self.source.idle_items(1) if item.currency == currency and item.last_movement is not None]
        if not items:
            return None
        days = (today - items[0].last_movement).days
        return f"{items[0].description} has not moved for {days} day{'' if days == 1 else 's'}."
